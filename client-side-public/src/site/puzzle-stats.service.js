import FetchService from "./fetch.service";
import { getTimePassed } from "./utilities";
class PuzzleStatsService {
  constructor() {
    this._puzzleStats = {};
  }
  getActivePlayerCountOnPuzzle(puzzleId) {
    const activePlayerCountService = new FetchService(
      `/newapi/puzzle-stats/${puzzleId}/active-player-count/`
    );
    return activePlayerCountService.get().then((playerCountData) => {
      const playerCount = {
        now: playerCountData.now,
        count: playerCountData.count,
      };
      return playerCount;
    });
  }
  getPlayerStatsOnPuzzle(puzzleId) {
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
    return puzzleStatsService.get().then((playerStats) => {
      const playerStatsWithTimeSince = {
        now: playerStats.now,
        players: playerStats.players.map(setPlayerDetails),
      };
      this._puzzleStats[puzzleId] = playerStatsWithTimeSince;
      return playerStatsWithTimeSince;
    });
    function _setPlayerDetails(item) {
      const playerDetail = Object.assign(
        {
          timeSince: getTimePassed(item.seconds_from_now),
          isRecent: getIsRecent(item.seconds_from_now),
        },
        item
      );
      return playerDetail;
    }
    function getIsRecent(secondsFromNow) {
      return secondsFromNow <= 5 * 60;
    }
  }
}
export const puzzleStatsService = new PuzzleStatsService();
