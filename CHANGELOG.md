# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Not every commit is added to this list, but many items listed are taken from the
git commit messages (`git shortlog 2.3.2..origin/develop`).

Types of changes

- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.

## [Unreleased] - ...
-->

## [Unreleased] - ...

Improving support for Vagrant and Virtualbox local environments. Also trying to
make it easier to get a working version on a local development machine without
needing to manually build stuff. The preferred local development setup is now
using Vagrant and VirtualBox. Terraform and Ansible will be used to deploy and
manage remote servers.

### Fixed

- Preview full image from generated puzzle images

### Added

- Terraform deployment for a development environment. Work in progress of [issue #92](https://github.com/jkenlooper/puzzle-massive/issues/92)
- Support for referral content in footer.
- Default vagrant setup uses a local cdn that is backed by a local fake s3 server.
- Script to move puzzle resources to be from s3 or back to being locally hosted.

### Changed

- Use latest stable version of NGINX. The install script will replace
  /etc/nginx/nginx.conf since it assumes it is in full control of the ngnix
  setup.
- The .htpasswd file is no longer created locally and uploaded to the server.

## [2.11.0] - 2021-06-01

Did a YouTube live stream going over some of the improvements to piece rendering
and with changes to the stacked pieces logic. Update: The stack pieces
functionality shown is actually old and doesn't really capture the current state
of things. I basically took a different approach then the one that was outlined
in the video.
[https://youtu.be/GLbO6n2JvMs](https://youtu.be/GLbO6n2JvMs)

### Fixed

- Restart chill app every 26 hours (temporary fix...)
- Stacked piece logic is _should_ be fixed and not break things

### Changed

- Active player count is now just within last 5 minutes instead of the last 14
  days.
- Update to latest piecemaker
- Update piece size and hot spot size
- Implement more accurate hotspot tracking
- Reject piece moves when too many pieces are stacked
- Show different cursors when interacting with pieces on a puzzle

### Added

- Stacked pieces show a border and change to grayscale to hint that joining of
  pieces are temporarily disabled

## [2.10.2] - 2021-03-20

Optimize response times when moving pieces.

Migrate script for this update: migrate_from_2_10_1_to_2_10_2.py

### Fixed

- Players without a cookie will be shown a reload page message when attempting
  to move a piece on a puzzle.

## [2.10.1] - 2021-03-14

### Added

- Unsplash batch upload form on admin page.
- Site config setting to auto approve submitted puzzles

### Fixed

- Scripts around provisioning TLS certificates with the Let's Encrypt certbot
  work better when doing blue/green deployments.
- Auto rebuild query correctly gets the preview_full of the puzzle it is
  rebuilding.

### Changed

- The skill level ranges for puzzles are now configurable via updating the .env
  file.
- Minimum puzzle counts that are used for scheduler tasks are now configurable.

## [2.10.0] - 2021-03-02

Bit icons have moved to a separate git repo and are no longer included in this
git repo. The source-media/bit-icons/ has a Makefile to resize these as needed.

Setup for implementing new features for puzzles. Initial one is adding the
hidden preview image for new puzzles.

If doing an in-place deployment then add `sudo apt -y install python-is-python3`.

Migrate script for this update: migrate_from_2_9_2_to_2_10_0.py

### Added

- The home page route can be configured to be something different then the most
  recent puzzle.
- A montage of all bit icons for each author will show on their bit icon author page.
- Show link back to bit icon author page for bit icons shown on player account page.
- Allow new puzzles to have the option of hiding the preview image
- Allow submitted and suggested puzzles to have the option of being private.
- Faster in-place deployments with quick-deploy.sh
- (Content) Three letter animal and insect bit icons.
- (Content) Generated bit icons from emoji characters

### Changed

- Specific content for a site is separated out into chill-data directory and
  'other' directories in templates, queries, and documents.
- Moved bit icons to puzzle-massive-content git repository.
- Credits page shows bit icon authors on separate pages
- Update bit icon expiration extend values
- Original puzzles that are unlisted can not be rebuilt

### Fixed

- Styleguide page is added if in development environment
- Include python-is-python3 to make sure that sudo uses python 3.

## [2.9.2] - 2021-01-30

### Changed

- Drop limit for same player concurrent piece moves
- Show ring around player bits when clicking on pieces
- Replace box shadow around pending piece movement with an hourglass icon
- Player bits stay on puzzle longer
- Don't show own player bit on puzzles

## [2.9.1] - 2021-01-24

### Changed

- Optimize puzzle preview load time

### Fixed

- The 'bump' button on puzzles that were in the queue were missing

## [2.9.0] - 2021-01-23

Improved how players can move pieces on a puzzle that is seeing lots of activity.

### Removed

- Redis keys that were used for tracking blocked players: "blockedplayers" and "blockedplayers:puzzle"
- Limits on puzzle pieces requests have been dropped in favor of caching the
  response

### Changed

- Optimized piece movement requests and moved piece movement latency to
  secondary menu on puzzle page.
- Switched build to use rollup instead of webpack.
- Show reload button when puzzle status changes
- Get wider range of puzzles when auto rebuilding
- Move latency info to secondary menu
- Hide puzzle karma points after passing threshold
- Reimplement dot cost for changing bit icon
- Puzzle piece movement is handled by separate process
- Puzzle piece transition uses a 'sneeze' effect for pieces moved by other players
- Increase blocked player timeouts each time a player reaches 0 karma points
- Hide player list for non recent players

### Added

- Puzzle rules configuration in the site.cfg
- Other piece movements are temporarily paused for that player when they are moving
  a piece. This allows the player to better join pieces that may have been
  moved by others.
- Shadows on pieces that have moved while paused
- Pieces data is cached and another endpoint is used to get any new piece movements since then.

### Fixed

- Duplicate puzzles showing up in gallery puzzle list that were from Unsplash.
  This fix requires executing the data fix sql:
  [data-fix-2.8.2-to-2.9.0.sql](queries/data-fix-2.8.2-to-2.9.0.sql)

## [2.8.2] - 2020-07-16

### Fixed

- New instances of unlisted puzzles remain unlisted.

## [2.8.1] - 2020-06-23

### Changed

- Show recently completed puzzle pieces
- Purge cache when puzzle status changes

### Fixed

- Fix rebuild freeze when using archive_and_clear

## [2.8.0] - 2020-06-20

Puzzle instance improvements and puzzle alert messages. Closes [#68](https://github.com/jkenlooper/puzzle-massive/issues/68).
Updated the development.md guide to be more user friendly.

### Changed

- Deleting puzzle instances that are not complete depends on last modified date
  and has a max dot cost of 1000. Puzzles that haven't been modified for
  a while can be deleted without costing any dots.
- Puzzle alerts when site goes down for maintenance as well as when the puzzle
  is being updated that would require players to reload.
- Update earned dots amount logic for piece joins. Unlisted puzzles do not earn any dots. However, the points for the player's score is still increased the same way as before. Earned dots are more closely aligned with the skill level range.
- Site settings include things that use to be set in constants.py.

### Added

- Players with an open puzzle instance slot can create copies of puzzles. These
  copies will copy the current piece positions of the source puzzle. The copy
  can not be publicly listed on the site since that would be confusing for
  players.
- Puzzle instances can have their piece positions reset by the owner at any
  time. Publicly listed puzzle instances can't have pieces reset since that
  would not be nice to other players.
- Show player puzzles other then just puzzle instances owned by that player.

### Fixed

- [Database locked issue](https://github.com/jkenlooper/puzzle-massive/issues/67) when running other scripts.
  All other apps connect to the sqlite database in read only mode. Chill app is
  the exception, but it doesn't write to the database. Scheduler will retry
  every 5 minutes if a http connection error happens when hitting the internal
  API URLs.
- Puzzles that have been recently modified show their recent status faster in
  the active puzzle list. The scheduler interval is every second now instead
  of every minute.

## [2.7.0] - 2020-05-17

### Changed

- Redesign of puzzle front page layout and header
- Update buttons to use new style
- Shorten auto-rebuild interval to keep at least the minimum amount of active
  puzzles per skill level. Did a hotfix on the live site (2020-05-10).

### Added

- Link to Puzzle Massive store which is currently a square site that allows
  players to buy puzzle instance slots.
- Style guide page when developing

## [2.6.1] - 2020-05-05

### Changed

- Home page includes a better description so search engines can index the site
  better.

### Fixed

- Hotlinking policy in web server config is less restrictive. Social media sites
  commonly add a query param to the pages that are shared. Did a hotfix on
  the live site to fix this (2020-05-04).

## [2.6.0] - 2020-05-03

Breaks everything, maybe. Then fixed everything, hopefully. Now more up to
date to the latest [jkenlooper/cookiecutter-website](https://github.com/jkenlooper/cookiecutter-website).

### Added

- New Puzzle Massive logo added to source-media.
- New favicon
- New open graph shareable image
- Included sponsor's online stores on buy stuff page.

### Changed

- More pages on the site are friendly to search indexing robots.
- Merge web server configs and clean up. Document pages go to /d/ route.
- Image upload size limit increased.
- Dropped piece movement rate restrictions per IP. Players on a shared VPN
  should have less errors once they claim or register their player account. The
  karma rules still apply per puzzle for IPs.
- Shorten player name automatic approval time to about 10 minutes.
- Improved footer layout and links.

## [2.5.2] - 2020-03-30

### Fixed

- Corrected adjacent piece logic when the piece group id is 0

## [2.5.1] - 2020-03-26

### Fixed

- Improved code to avoid causes of multiple immovable piece groups. These fixes
  were not 100% confirmed to fix the possible causes of this bug
  ([issue #63](https://github.com/jkenlooper/puzzle-massive/issues/63)).

  A python script
  ([fix_immovable_piece_groups_in_redis.py](api/api/jobs/fix_immovable_piece_groups_in_redis.py))
  was added to better find puzzles with the problem.

### Changed

- Hide latency on completed puzzles
- Hide puzzle completed alert after 5 seconds
- Add puzzle outline background color back in

## [2.5.0] - 2020-02-22

Cleaned up _some_ of the code around puzzle piece movements.

### Changed

- Switch from websockets to server-sent events for piece movement updates
- Show puzzle outline on top layer
- Refactor piece moving, joining, and stacked logic
- Allow selected piece to stay selected even when the group it is in moves

### Added

- Show latency in bottom right of outline
- Show message when puzzle is completed, frozen, or deleted

## [2.4.1] - 2020-01-05

### Added

- A toggle button on the puzzle page will draw a box around each piece that is
  still movable. This will help players find hidden pieces that blend into the
  background.

### Fixed

- Cache on message, and puzzle resources has been corrected

### Changed

- The piece count list on search page now matches the skill level range for
  queued puzzles. Players will still see their previous selection since it is
  stored in localStorage.
- Use the submitted description for Unsplash photos and fallback to description
  from Unsplash if missing. Sometimes Unsplash photos have strange
  descriptions for their photos.
- The puzzle page now shows bit icons with the player names next to
  their piece movements.

## [2.4.0] - 2019-12-14

Redesign with a new puzzle search page. Old queue page has been replaced.

Added the ability for players to add a name for their bit icon. Players can also
register their e-mail address with their account. Login by e-mail can then be
accomplished by going through a reset login process.

New puzzle instances and slots are a new paid for feature, but not automated at
the moment.

### Changed

- New players are shown a new player page
- Show player id in base 36 for no bits
- Add shareduser to user flow, drop cost to bit icon
- Limit to active puzzles, use a queue for others
- Show approved username next to bit

### Added

- Puzzle instances and puzzle slots
- Support for puzzle variants
- Document use of chill dump and chill load
- Allow player instance puzzles to be unlisted
- Add player detail view for admin
- Show pieces when puzzle is frozen
- Add puzzle list page
- Add puzzle image card
- Add testdata script
- Add bump button for moving queue puzzles
- Add player email form on profile page
- Show total active players near footer
- Add email verification and player claim
- Add menu and clean up profile page
- Setup for reset login by email form

### Removed

- Deprecate puzzle queue pages and redirect
- Remove up/down buttons for pm-ranking

### Fixed

- Extend user cookie expiration correctly
- Fix error for first piece move on puzzle

## [2.3.2] - 2019-07-26

Run janitor task after pieces request finish.

## [2.3.1] - 2019-06-11

Minor changes to homepage and auto rebuild handling of puzzles.

## [2.3.0] - 2019-05-28

Switch to python 3. Improve development guide.

### Added

- Scheduler process to auto rebuild and other tasks
- Add redis keys for tracking score/rank
- Replace player-ranks api
- Add total player count and active players

### Fixed

- Improve cleanup of completed puzzles

## [2.2.0] - 2019-03-21

Start using web components and typescript.

### Added

- Add prettier package
- Add stylelint
- Make the domain name configurable
- Improve docs for developing and deploying
- Show license in footer, update contribute info
- Show message for unsupported browsers
- Store anonymous login link locally
- Add logout link

### Removed

- Old angularJS code has been replaced
- Remove minpubsub

### Deprecated

- Drop support for older browsers

### Fixed

- Fix error with concurrent pieces alert
- Fix missing bit icon

## [2.1.4] - 2019-02-03

Improved build process for JS. Cleaned up the README and development guide.

## [2.1.3] - 2019-01-20

### Added

- Set rebuild puzzle to change piece count
- Implement rebuild status

## [2.1.2] - 2019-01-15

Include a note to update policy on image magick when creating a new server. This
allows the puzzle generating process to create larger puzzles.

### Fixed

- Prevent reset of puzzles that used old render
- Fix query on puzzle reset

## [2.1.1] - 2019-01-12

### Fixed

- Remove check for immovable on token request
- Fix migrate puzzle file script

## [2.1.0] - 2019-01-08

### Added

- Improved puzzle upload handling.
- Add checks for puzzle piece movements.

## [2.0.1] - 2018-10-28

Clean up some documentation on deployment instructions. Fix some minor issues
with SQL on queue page.

## [2.0.0] - 2018-10-06

Started a new direction for this project to be more open and now hosted on
GitHub.

### Moved

- Migrate all files from GitLab repo
