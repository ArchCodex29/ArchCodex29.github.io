# Creating a free, Markdown-based, personal portfolio

In this article you can read about portfolios, why create one and how to build and host your own using free and readily available tools. 

Whether personally or professionally, chances are you have created at least one project. A piece of decorative art, a small website or a song. Probably even more than one. And it's natural you want to share these projects with others.

That's what **portfolios** are for. A collection of "projects" we have worked on that we want to share or showcase. Traditionally these portfolios were big dossiers full of pages and pictures, but in these days is more common (and practical) to have a "digital portfolio". This is where a blog website comes in handy.

In my case, most of (if not all of) my projects are software/programming related. Which made me *not* choose one of the hundred blog platforms out there and instead look into creating my own. I already write my notes and docs in Markdown, so it would be an added advantage if it were Markdown-based. And, if possible, have it up and running for free. 

With this goals in mind, this project was born.

> If you're not familiar with Markdown, it's a language used to write and format text documents. Think of it as plain text, with added "syntax" to perform the common text edits like *italic* and **bold**.

## Why create a portfolio ? 

As I have written above, the purpose for a portfolio is to share projects with others. 

In my case, I created this portfolio to :
- Showcase my projects to anyone interested. 
  - May be someone looking for inspiration to create something I have already done.
  - May be a recruiter curious about what I do outside of work.
- Document my projects for future reference.
  - Useful for me to consolidate what I've learnt during a given project, since I have to understand what I have created to be able to write about it.
  - Can be read by others interested in replicating what they are seeing.
- (Bonus) Since I am building this myself, this portfolio counts as a project to show in said portfolio. Portfolio-ception.

## Building the portfolio

After searching for what type of tools are available to create blog platforms and matching those to what I wanted to achieve - a free, markdown-based, blog website - I have come across two that can be combined to achieve just what I wanted.

- For the blog platform itself, I have found the [Hugo](https://gohugo.io) framework which allows us to generate a website from Markdown files.
- For hosting the website, we can leverage [Github Pages](https://pages.github.com) to do just that. It allows us to host a website built from a public Github repository. 
  - And since we will want to save this project (plus all the content we write) somewhere, it takes care of that too.

> Note: If you want to build this for yourself but you're not familiar with "code", don't worry. Most of the needed steps are configurations, so you can still follow along.

So, with all this in mind, here's what we need to get started :
- A free [GitHub](https://github.com) account (counts both as our repository and deploy server, using [GitHub Pages](https://pages.github.com))
- Git Version Control + Visual Studio Code
  - You can use any other code editor of your choice. I mention this one since I have created some VSCode-specific configs and shortcuts, but can be skipped.
- [Hugo](https://gohugo.io) framework + a suitable theme (I picked [Hugo Coder](https://github.com/luizdepra/hugo-coder))
- Python installed (in order to be able to run one utility script)
  - In theory, you don't "need" to have it installed in order to use this project, but it will help with local testing before syncing changes to the repository.

After we are done building all the needed parts, the good thing is we won't have to actively interact with most of the elements mentioned. Just focus on what matters - the Markdown files.

You can also check my [portfolio repository](https://github.com/ArchCodex29/ArchCodex29.github.io) if you want to see the final result or copy a given file.

> Curious how viable this plan is ? Well, this article - this website - was built with this plan up here. If you're reading this, it's working!

### Setting up the repository

In order to have a place to both store our files and host our website, we need to create a new public `Repository` in our GitHub account (Create one if you haven't already. It's free).

You can choose any name you like for the repository, of course. However, if you would like a suggestion, I suggest you name it "<your_nickname_here>.github.io". So, in my case, since the nickname is "ArchCodex29", I named my portfolio repo "ArchCodex29.github.io".

Why this specific naming, you ask ? 

With GitHub Pages, when we publish one website from one of our repositories, by default it publishes "under" that generated domain I just mentioned as a subfolder. For example, if I have named the repository "portfolio", it would've been published under "ArchCodex29.github.io/portfolio". If this is the url you would like for yours, then go ahead and name it as such. 

If we want our portfolio directly under our generated domain, however, we can do so by using the naming schema I wrote before and Github by default will do just that! Consider it a little "easter egg", if you will.

With the name chosen and the repository created, all that's left is to change one quick setting.

Head over to the repository's `Settings` (last tab on the top row) and then look for a menu called `Pages`. You should see a section named `Build and deployment` with a dropdown menu. Change it's value to "Github Actions" and you're set!

You can now clone the repository on your own computer and start preparing the project.

> If you're new working with Git, don't worry. On a blank repository, GitHub shows you instructions on what commands to run to get started. Later on, to "send" your changes from your computer to the online repository, VS Code also has a clear interface to do so.

### Setting up the project

Now that we have a place to host our project, it's time to start creating our portfolio.

This section will be similar to the guidance you can find on Hugo's page. In fact, it was on top of said guides I have built this project, so I strongly suggest taking a look at those, with a special focus on the [Quick Start](https://gohugo.io/getting-started/quick-start/) and the [Hosting on GitHub Pages](https://gohugo.io/host-and-deploy/host-on-github-pages/).

The first step is to [install Hugo](https://gohugo.io/installation/). You can install it directly on your computer (the easy, normal path) or use a `Docker` dev container or, if you are using Windows, use `Windows Subsystem for Linux (WSL)` to to both isolate the dependencies and have access to a "Linux experience" during this, in lack of better words.

> If you didn't recognize most of those terms I just mentioned, it's fine. You can simply install the required tools on your PC and keep on following the guid. However, if you're eager to learn, I'd suggest reading about how to set up WSL (will be useful on your future projects) then coming back to this guide.

For the remaining of this section, I will proceed with a setup of Windows + WSL (for the dependencies + running particular commands and tasks) in mind.

To install Hugo on your WSL environment you just need to use your Distro's package manager. You can check the exact command on the install link above, but assuming you're using a common Debian distro, it should be something like this:

```bash
sudo apt install hugo
```
With this tool installed, we can now use it to create the project. We will also need to pick a theme to go along with it. I will be using [Hugo Coder](https://github.com/luizdepra/hugo-coder) as my theme of choice. You can also go to ahead and pick yours from this [Hugo Themes](https://themes.gohugo.io) page, but don't forget to check the chosen template's repository since some templates have specific instructions on how to set them up.

Here are the commands needed to create a folder, create a new project with the chosen template

```bash
hugo new project site
cd site
git submodule add https://github.com/luizdepra/hugo-coder.git themes/hugo-coder
echo "theme = 'hugo-coder'" >> hugo.toml
hugo server
```

If all goes well, you will see in your terminal the local URL for the website. Follow it and you should see the sample home page.

Later on, you will probably want to change some settings to turn this into *your* portfolio. When that moment arrives, I recommend reading about [Hugo Configuration](https://gohugo.io/configuration/introduction/).

On a typical Hugo project, this would be the part where you would go to the generated `Content` folder on our project and start creating your own sub folders and markdown files, which would then be interpreted by Hugo and turned into source files for our website. You would also write some "metadata" on top of each markdown file to allow you to set some "specific" info for each post, such as the title, the creation date or the series it belongs to, in a format that the Hugo framework has defined.

*However*, when I started creating this project for myself, I did not want to "tie" my markdown files specifically to Hugo (or any other tool, for that matter). In fact, when I am actively writing blog posts (such as this one) I don't even want to *see* any code files nor the terminal. 

So, to improve the base workflow for my needs and wants, I decided to write all my "raw" markdown files *outside* the site folder and create a Python script that, when executed, copies the files to the respective locations *inside* the `site` folder, calculating and adding any "metadata" to those files as needed. This way, I don't have to think about Hugo-specific semantics while still taking advantage of them.

You can find the full script on this portfolio's repository, under `.github\scripts\sync_content.py`. After defining which folders/files to watch for, where to copy them and which metadata to generate, I grabbed the specification and had Claude generate the script in my stead. If, in the future, there's any change you'd like for yourself (for example, you want to automatically add "tags" based on some criteria), and you're not well versed in Python, I suggest you do something similar. Don't forget to review the results!

By default, it reads any folder other than the `site` itself. Also supports subfolders, where it automatically creates a "series" for it. For example, I have a `gamedev` folder with a `nanoswarm` subfolder. All blog posts I write under this folder will belong to the "nanoswarm" series. I can also write on blog posts and not have them automatically published by adding ".draft" to the file name. So, a file named "my project.md" would be "my project.draft.md". Then I can just remove it when it's done for publishing.

Also, important to mention : The script not only copies the markdown files to their respective location under `content`, it will also copy other assets (images, gifs and the like) to `static\images` so they can be presented to the readers too!

To further aid me during all this, I have also created a couple of VS Code tasks to run the common commands for me, instead of having to memorize them and write them every single time. You can find them under `.vscode\tasks.json`. You should find tasks to run the before-mentioned "sync" script, build and run the website using Hugo and so on. You can run tasks in VS Code by pressing `F1` > type `Run Task` and press enter > picking an available task.

Here's an example of one of them :

```json
{
  "label": "Hugo: Sync content",
  "detail": "Run the sync script",
  "type": "shell",
  "command": "python .github/scripts/sync_content.py",
  "options": {
    "shell": {
      "executable": "wsl",
      "args": ["-d", "ArchDaemon"]
    }
  },
  "group": "none",
  "presentation": {
    "reveal": "always",
    "panel": "shared",
    "clear": true
  }
},
```

One thing to watch out for : these tasks are adapted to run directly under WSL, using an instance named "ArchDaemon". Adjust the tasks to use your WSL's instance name or just remove the section `options` section if you're not using WSL. (You could also adapt it to run inside an ephemoral Docker instance, for example. That could be fun.)

Since I am writing about useful files you should copy, allow me to mention one more. Under `.github\workflows\hugo.yml` you will find a GitHub Action named "Sync content, Build and Deploy" which allows GitHub to, well, do just that! It is set up to run automatically when you push your changes to the `main` branch (you can change to any branch name) and to run manually by you. It will use the Python script to copy your original files to their destinations, build the website source files using Hugo and then publish them to your (free!) GitHub Page website. This GitHub Action file is based on Hugo's own suggested file, to which I have added a few steps to handle the custom script I have created.

And finally (this bit is mostly a quality-of-life, but I like it), I have also created a few ".code-workspace" files to allow me to open the project with VS Code and focus on a particular section of the project. I have created a `portfolio-dev.code-workspace` that, when used, shows me only the Hugo website and relevant code folders, and a `portfolio-write.code-workspace` that only shows me the folders I have chosen with my original markdown files (and the workspace I use the most now). 

With all these files in place, you can test this by :
- Create your first folder to store your Markdown files. For example "projects"
- On this folder, create a sample "test.md"
- Run the task `Hugo: Sync and Serve`
- Check locally if everything is running and showing as intended
- If you're happy with the results, push your progress to the repository
- Wait for a minute or two while GitHub runs our Action (you can also check the progress under the `Actions` tab on your repository page)
- Visit your newly published portfolio by going to <your_nickname_here>.github.io

### Expected workflow

With all the different pieces in place, here's the workflow I use when I am writing blog posts in this project :

- Open the "write" workspace, which shows me only the source markdown files
- Create a new .md file or just write on an existing one (may or may not be a draft)
- At the end of the writing session, commit and push the changes
- Automatically, the Github Action triggers, building and publishing a new version of the website

If I ever have the need to update the website configuration itself or other similar sections, I can either open the "dev" workspace or just the plain project folder. Can be useful to check how the rendered website looks locally after a big change before publishing, for example.

## Closing Notes

After creating this project (which I mention in my portfolio, which is a project), you should be able to write your blog posts about any topic you want and publish it online for everyone to see, without spending a cent. 
For me personally, not only I was able to create a portfolio for my own use, I was also able to learn about `Hugo` and `GitHub Pages` (a feature I already wanted to try out), so it was a worthy project for me.

Hope this blog post was helpful in any way.  
Got a question or just wanna discuss something? Feel free to reach out!  
And thank you for reading!