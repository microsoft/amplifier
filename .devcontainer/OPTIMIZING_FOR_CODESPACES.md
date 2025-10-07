# Tips for Optimizing Your Codespaces Experience

This project is designed to work seamlessly with **[GitHub Codespaces](https://docs.github.com/en/codespaces/about-codespaces/what-are-codespaces)** — a cloud-based development environment that lets you start coding instantly without local setup. The tips below will help you get the most out of your Codespaces experience, keeping things fast, reliable, and tuned to your workflow.

---

## Change Your Default Editor to Run Locally [RECOMMENDED]

By default, new GitHub Codespaces open in **Visual Studio Code for the Web** — a lightweight, zero-install option that runs entirely in your browser. It’s great for getting started quickly, especially on devices that can’t run VS Code natively.

That said, most developers will have a smoother experience running **Visual Studio Code locally**. The local editor connects directly to your Codespace container running in the cloud, giving you:

* A faster, more responsive interface
* Fewer connection drops
* Access to your local extensions and settings
* Better support for local port forwarding when testing services inside the container

To make VS Code your default editor for Codespaces:

1. In GitHub, click your profile picture → **Settings**.
2. In the left sidebar, select **Codespaces**.
3. Under **Editor preference**, choose **Visual Studio Code**.

From now on, your Codespaces will automatically open in your local VS Code — while everything still runs remotely in the GitHub-hosted environment. You can always switch back to the web editor anytime using the **…** menu when launching a Codespace.

---

## Use a Dotfiles Repository for Custom Configuration [RECOMMENDED]

A **dotfiles repository** is the easiest way to make your Codespaces feel like home. GitHub can automatically clone your dotfiles into every new Codespace, applying your preferred environment variables, shell configuration, and editor settings the moment it starts.

Here are a few ideas for what to include in your dotfiles repo:

* Environment variables in `.bashrc` or `.zshrc`
* Editor preferences in `.editorconfig` or `.vscode/settings.json`
* Git configuration (name, email, aliases) in `.gitconfig`

To enable dotfiles for your Codespaces:

1. In GitHub, click your profile picture → **Settings**.
2. In the left sidebar, select **Codespaces**.
3. Check **Automatically install dotfiles**.
4. Choose your dotfiles repository from the dropdown.

If you don’t already have a dotfiles repository, see [GitHub’s guide to personalizing Codespaces with dotfiles](https://docs.github.com/en/codespaces/setting-your-user-preferences/personalizing-github-codespaces-for-your-account#dotfiles) for setup instructions and best practices.

You can also create a separate `dotfiles` repo specifically for this project if you prefer to keep your personal environment isolated.

Once enabled, every new Codespace you spin up will automatically configure itself just the way you like it — no extra setup required.

---

## Prebuild Your Codespace for Faster Startups [OPTIONAL]

GitHub Codespaces supports **prebuilds**, which let you snapshot a ready-to-code environment. Instead of waiting for container setup and dependency installation, your Codespace can launch in seconds using the prebuilt version.

Prebuilds are already configured for this project’s main repository, but you can set them up in your own fork as well:

1. Go to your fork of the repository.
2. Click **Settings** → **Codespaces** in the left sidebar.
3. Click **Set up prebuild**.
4. Select the branch you want to prebuild (usually `main`).
5. (Optional) Under **Region availability**, deselect regions other than the one closest to you.
6. Click **Create**.

Once created, GitHub will automatically maintain your prebuild so it stays up to date with your branch. The next time you create a Codespace, it’ll be ready to go — no waiting, no setup delay.
