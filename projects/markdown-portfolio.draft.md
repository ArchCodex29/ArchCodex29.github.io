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

After we are done building all the needed parts, the good thing is we won't have to actively interact with most of the elements mentioned. Just focus on what matters - the Markdown files.

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

### Setting up the project


### Expected workflow

With all the different pieces in place, here's the workflow I use when I am writing blog posts in this project :

- Open the "write" workspace, which shows me only the source markdown files
- Create a new .md file or just write on an existing one (may or may not be a draft)
- At the end of the writing session, commit and push the changes
- Automatically, the Github Action triggers, building and publishing a new version of the website

If I have the need for updating the website configuration itself or other similar sections, I can either open the "dev" workspace or just the plain project folder. Can be useful to check how the rendered website looks locally after a big change before publishing, for example.

## Closing Notes

