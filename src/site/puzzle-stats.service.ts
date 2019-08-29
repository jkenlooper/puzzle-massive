import FetchService from "./fetch.service";
import { getTimePassed } from "./utilities";

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
  isRecent: boolean;
}

interface PuzzleStats {
  [puzzleId: string]: PlayerStatsData;
}

export interface PlayerCountData {
  now: number;
  count: number;
}

class PuzzleStatsService {
  _puzzleStats: PuzzleStats = {};
  constructor() {}

  getActivePlayerCountOnPuzzle(puzzleId: string): Promise<PlayerCountData> {
    const activePlayerCountService = new FetchService(
      `/newapi/puzzle-stats/${puzzleId}/active-player-count/`
    );

    return activePlayerCountService
      .get<PlayerCountData>()
      .then((playerCountData) => {
        const playerCount = {
          now: playerCountData.now,
          count: playerCountData.count,
        };
        console.log("getActivePlayerCountOnPuzzle", puzzleId);
        return playerCount;
      });
  }

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
          isRecent: getIsRecent(item.seconds_from_now),
        },
        item
      );
      return playerDetail;
    }

    function getIsRecent(secondsFromNow: number): boolean {
      return secondsFromNow <= 5 * 60;
    }
  }
}

export const puzzleStatsService = new PuzzleStatsService();
