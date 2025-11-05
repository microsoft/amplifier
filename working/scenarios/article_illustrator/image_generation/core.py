"""Image generation orchestration."""

import asyncio
from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models import GeneratedImage
from ..models import ImageAlternatives
from ..models import ImagePrompt
from .clients import DalleClient
from .clients import GptImageClient
from .clients import ImagenClient

logger = get_logger(__name__)


class ImageGenerator:
    """Orchestrates image generation across multiple APIs."""

    def __init__(
        self,
        apis: list[str],
        output_dir: Path,
        cost_limit: float | None = None,
    ):
        """Initialize image generator.

        Args:
            apis: List of API names to use (imagen, dalle, gptimage)
            output_dir: Directory for output images
            cost_limit: Optional cost limit for generation
        """
        self.output_dir = output_dir
        self.cost_limit = cost_limit
        self.total_cost = 0.0

        # Initialize requested clients
        self.clients = {}
        for api in apis:
            if api == "imagen":
                self.clients[api] = ImagenClient()
            elif api == "dalle":
                self.clients[api] = DalleClient()
            elif api == "gptimage":
                self.clients[api] = GptImageClient()

    async def generate_images(
        self,
        prompts: list[ImagePrompt],
        save_callback=None,
    ) -> list[ImageAlternatives]:
        """Generate images for all prompts.

        Args:
            prompts: List of image prompts
            save_callback: Optional callback after each image (for state saving)

        Returns:
            List of image alternatives for each prompt
        """
        logger.info(f"Generating images for {len(prompts)} prompts")

        results = []
        for i, prompt in enumerate(prompts):
            try:
                # Check cost limit
                if self.cost_limit and self.total_cost >= self.cost_limit:
                    logger.warning(f"Cost limit reached: ${self.total_cost:.2f}")
                    break

                # Generate alternatives
                alternatives = await self._generate_alternatives(prompt, i)

                if alternatives:
                    results.append(alternatives)
                    logger.info(
                        f"Generated {len(alternatives.alternatives) + 1} images for prompt {i + 1}/{len(prompts)}"
                    )

                    # Save state after each expensive operation
                    if save_callback:
                        await save_callback(results, self.total_cost)

            except Exception as e:
                logger.error(f"Failed to generate images for prompt {i + 1}: {e}")
                continue

        logger.info(f"Total generation cost: ${self.total_cost:.2f}")
        return results

    async def _generate_alternatives(self, prompt: ImagePrompt, index: int) -> ImageAlternatives | None:
        """Generate images from multiple APIs for one prompt.

        Args:
            prompt: Image prompt
            index: Prompt index

        Returns:
            Image alternatives or None if failed
        """
        # Prepare output paths
        images_dir = self.output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Generate from each API in parallel
        tasks = []
        for api_name, client in self.clients.items():
            if not await client.check_availability():
                logger.warning(f"{api_name} API not configured, skipping")
                continue

            output_path = images_dir / f"{prompt.illustration_id}-{api_name}.png"
            tasks.append(self._generate_single(client, api_name, prompt, output_path))

        if not tasks:
            logger.error("No APIs available for generation")
            return None

        # Run generations in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        generated_images = []
        for result in results:
            if isinstance(result, GeneratedImage):
                generated_images.append(result)
                self.total_cost += result.cost_estimate
            else:
                logger.error(f"Generation failed: {result}")

        if not generated_images:
            return None

        # Select primary image (first successful one for now)
        primary = generated_images[0]
        alternatives = generated_images[1:] if len(generated_images) > 1 else []

        return ImageAlternatives(
            illustration_id=prompt.illustration_id,
            primary=primary,
            alternatives=alternatives,
            selection_reason="First successfully generated image",
        )

    async def _generate_single(self, client, api_name: str, prompt: ImagePrompt, output_path: Path) -> GeneratedImage:
        """Generate a single image from one API.

        Args:
            client: API client
            api_name: Name of the API
            prompt: Image prompt
            output_path: Output file path

        Returns:
            Generated image

        Raises:
            Exception: If generation fails
        """
        logger.info(f"Generating {api_name} image: {prompt.full_prompt[:50]}...")

        try:
            url, cost = await client.generate(
                prompt=prompt.full_prompt,
                output_path=output_path,
                params={"quality": "standard"},  # Use standard quality for cost efficiency
            )

            return GeneratedImage(
                prompt_id=prompt.illustration_id,
                api=api_name,  # type: ignore[arg-type]
                url=url,
                local_path=output_path,
                generation_params={"quality": "standard"},
                cost_estimate=cost,
            )

        except Exception as e:
            logger.error(f"Failed to generate {api_name} image: {e}")
            raise
