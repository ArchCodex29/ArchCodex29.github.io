# improvement ideas

- group dev blogs in folders
  - either 1 folder per blog
  - or 1 folder per blog *assets* + 1 .md file
- create snippet files as *assets* for each blog
  - on the original file, link them directly like [this](file.md)
- on deploy, add a new job to manage gists
  - should run before the build/deploy of the page
  - in the generated site contents, the file snippet link should be replaced with a gist link (hugo shortcode)