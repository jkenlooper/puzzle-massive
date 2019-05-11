import FetchService from "./fetch.service";

export interface PlayerStatsData {
  now: number;
  players: Array<PlayerDetail>;
}

interface PlayerData {
  bitactive: boolean;
  icon: string;
  id: number;
  rank: number;
  score: number;
  seconds_from_now: number;
}

export interface PlayerDetail extends PlayerData {
  timeSince: string;
}

interface PuzzleStats {
  [puzzleId: string]: PlayerStatsData;
}

class PuzzleStatsService {
  _puzzleStats: PuzzleStats = {};
  constructor() {}

  getPlayerStatsOnPuzzle(puzzleId: string): Promise<PlayerStatsData> {
    const puzzleStats = this._puzzleStats[puzzleId] || {
      now: 0,
      players: [],
      queue: [],
    };
    if (puzzleStats.now) {
      return Promise.resolve(puzzleStats);
    }

    const setPlayerDetails = _setPlayerDetails.bind(this);

    const puzzleStatsService = new FetchService(
      `/newapi/puzzle-stats/${puzzleId}/`
    );

    return puzzleStatsService.get<PlayerStatsData>().then((playerStats) => {
      const playerStatsWithTimeSince = {
        now: playerStats.now,
        players: playerStats.players.map(setPlayerDetails),
      };
      this._puzzleStats[puzzleId] = playerStatsWithTimeSince;
      return playerStatsWithTimeSince;
    });

    function _setPlayerDetails(item: PlayerData): PlayerDetail {
      const playerDetail = <PlayerDetail>Object.assign(
        {
          timeSince: getTimePassed(item.seconds_from_now),
        },
        item
      );
      return playerDetail;
    }

    function getTimePassed(secondsFromNow: number): string {
      let timePassed = "";

      if (secondsFromNow < 60) {
        timePassed = "less than a minute";
      } else if (secondsFromNow < 2 * 60) {
        timePassed = "1 minute";
      } else if (secondsFromNow < 60 * 60) {
        timePassed = `${Math.floor(secondsFromNow / 60)} minutes`;
      } else if (secondsFromNow < 60 * 60 * 2) {
        timePassed = "1 hour";
      } else if (secondsFromNow < 60 * 60 * 24) {
        timePassed = `${Math.floor(secondsFromNow / 60 / 60)} hours`;
      } else if (secondsFromNow < 60 * 60 * 24 * 2) {
        timePassed = "1 day";
      } else if (secondsFromNow < 60 * 60 * 24 * 14) {
        timePassed = `${Math.floor(secondsFromNow / 60 / 60 / 24)} days`;
      } else {
        timePassed = "a long time";
      }
      timePassed = `${timePassed} ago`;
      return timePassed;
    }
  }
}

export const puzzleStatsService = new PuzzleStatsService();
