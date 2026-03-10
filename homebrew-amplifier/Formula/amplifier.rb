class Amplifier < Formula
  desc "AI-powered modular development assistant"
  homepage "https://github.com/microsoft/amplifier"
  url "https://github.com/microsoft/amplifier/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  head "https://github.com/microsoft/amplifier.git", branch: "main"

  depends_on "uv"
  depends_on "python@3.12"

  # Pre-built Python wheels (e.g. pydantic_core) have compiled extensions
  # whose Mach-O headers cannot be rewritten by Homebrew's relocator.
  # This is harmless — the extensions work correctly without relocation.
  skip_clean "libexec"

  def install
    python = Formula["python@3.12"].opt_bin/"python3.12"
    venv = libexec

    # uv sync respects [tool.uv.sources] and uv.lock for reproducible installs
    # (including git-sourced packages not yet published to PyPI)
    ENV["UV_PROJECT_ENVIRONMENT"] = venv.to_s
    system "uv", "sync", "--frozen", "--no-dev", "--python", python

    (bin/"amplifier").write_env_script(venv/"bin/amplifier", PATH: "#{venv}/bin:$PATH")
  end

  test do
    assert_match "amplifier", shell_output("#{bin}/amplifier --version")
  end
end
