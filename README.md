# Puzzle Massive

A Massively Multiplayer Online Jigsaw Puzzle as a web application. Jigsaw
puzzles are made from randomly generated classic interlocking pieces and can be
5000+ pieces. Players can collaborate on the same jigsaw puzzle in real time.
Other player's piece movements are moderated automatically in order to prevent
abusive behavior.

**A live version is hosted at [puzzle.massive.xyz](http://puzzle.massive.xyz).**

Bugs and feature requests can be tracked via the projects source code repository
https://github.com/jkenlooper/puzzle-massive/issues
or send an email to puzzle-massive-bug@pm.me with a description.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

[![code style: prettier](https://img.shields.io/badge/code%20style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

## Local Install Instructions (TL;DR)

Minimal setup to get it running on your local machine at
[http://localhost:38682/](http://localhost:38682/).

```bash
cd client-side-public && make && cd -
vagrant up
vagrant provision --provision-with shell-init-dev-local
vagrant provision --provision-with shell-testdata-puzzles-quick
```

---

**More documentation is available within the [docs directory](docs/).**

- [Mockups guide](mockups/README.md) for only editing CSS and HTML or otherwise
  creating mockups of proposed changes. This doesn't require building or running
  the full site locally.
- [Local development guide](docs/development.md) for getting a local version
  running on your own machine.
- [Deployment guide](docs/deployment.md) for deploying to a live server. This
  covers both in-place deployments and blue-green (stateful swap) deployments.
- [Infrastructure as Code](_infra/README.md) documents how the project uses
  [DigitalOcean](https://m.do.co/c/686c08019031) and [Terraform](https://www.terraform.io/)
  for deploying to Development, Test, Acceptance, and Production environments.

## Getting Help

Ask questions on:

- [Puzzle Massive Discussions](https://github.com/jkenlooper/puzzle-massive/discussions)
- [Chat on Discord](https://discord.gg/uVhE2Kd)
- [Slack](https://join.slack.com/t/puzzlemassive/shared_invite/zt-v2csgv8y-Ldl93sNb3Gcm~NiWt3g5UA)

I try to monitor the Puzzle Massive chat channels on
[Discord](https://discord.gg/uVhE2Kd)
and
[Slack](https://join.slack.com/t/puzzlemassive/shared_invite/zt-v2csgv8y-Ldl93sNb3Gcm~NiWt3g5UA)
. This project is slightly complex with
a few moving pieces (pun intended); that being said, there is a good chance that
a piece or two are missing when putting the project together. If you have ran
into a problem getting this project working on your own machine; please ask for
help. I'm looking to improve the process where I can and am looking for more
experience helping others in web development stuff like this.

## Change Log and History

This project has been moved to GitHub with a fresher git commit history. The
previous git commit history is available upon request. I've chosen to make
Puzzle Massive an open source project under the GNU Affero General Public
License.

**[Changelog since 2.0.0](CHANGELOG.md)**

## License

Puzzle Massive. An online multiplayer jigsaw puzzle.
Copyright (C) 2021 Jake Hickenlooper

Only the source code that is used for Puzzle Massive is licensed under the
[GNU Affero General Public License](https://choosealicense.com/licenses/agpl-3.0/).
Content included in this project is licensed under the
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
License.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.digitaloceanspaces.com/WWW/Badge%203.svg)](https://www.digitalocean.com/?refcode=686c08019031&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)
