# ArchCodex29.github.io

My Porfolio repository. A place where I write about .... a bit of everyting, really.

To create this portfolio, I'm using :
* [Hugo](https://gohugo.io/)
* [Hugo Coder](https://github.com/luizdepra/hugo-coder)
* [Github Pages](https://docs.github.com/en/pages)

Been using Markdown for most of my docs, so using a tool that can convert them to a working website is great!
Only thing I have added on top of the basic Hugo usage is a script that allows me to "separate" the original .md files from the final ones that are used for the content generation

Why ? Because when I am writing a given blog post I don't want to have to "think" about specific Hugo frontmatter, or moving images to the correct static folder. So, that script plus a few .code-workspace files and I can open a VS Code instance with *only* what I need at the time

## Embedding a GitHub Gist

In a source Markdown file, provide the Gist owner's GitHub username and the Gist's 32-character identifier. Add `file` to embed one specific file:

```text
{{< gist user="octocat" id="0123456789abcdef0123456789abcdef" >}}
{{< gist user="octocat" id="0123456789abcdef0123456789abcdef" file="example.py" >}}
```

Hugo renders GitHub's live embed script and a direct link to the Gist. Visitors' browsers load the embed from GitHub.