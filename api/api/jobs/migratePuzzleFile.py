"""
Meant to run periodically to migrate existing puzzles.  Will not handle rerendering puzzles; just changing their status to rebuild.
- If AWS S3 hosted puzzle resources; download original.jpg and create new preview_full if it isn't unsplash
- If preview_full is source.unsplash create custom size with api and update PuzzleFile
- If source.unsplash; update description with links to photographer and unsplash.  Include photo description on next line.
"""
# TODO: Update description for unsplash photos.  May need to have description able to handle some HTML like anchor links? maybe strip tags?
# Photo by Annie Spratt / Unsplash
# [description]
result = cur.execute("select name, url from PuzzleFile where puzzle = :puzzle and name = :name and url like :url", {
    'puzzle': puzzle['id'],
    'name': 'pieces',
    'url': 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%'
    }).fetchone()
if result:
    # TODO: migrate off of S3

result = cur.execute("select name, url from PuzzleFile where puzzle = :puzzle and name = :name and url like :url", {
    'puzzle': puzzle['id'],
    'name': 'preview_full',
    'url': 'https://source.unsplash.com/%'
    }).fetchone()
if result:
    # TODO: fix preview_full url

