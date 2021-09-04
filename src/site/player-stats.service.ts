import FetchService from "./fetch.service";

type PlayerStatsCallback = () => any;

interface PlayerStatsResponse {
  totalActivePlayers: number;
}
export interface PlayerStatsData extends PlayerStatsResponse {
  hasError: boolean;
  isReady: boolean;
}

class PlayerStatsService {
  private fetchStatsService: FetchService;
  private listeners: Map<string, PlayerStatsCallback> = new Map();
  private pollingInterval = 1 * 60 * 1000; // one minute
  data: PlayerStatsData = {
    hasError: false,
    isReady: false,
    totalActivePlayers: 0,
  };

  constructor() {
    this.fetchStatsService = new FetchService(`/newapi/player-stats/`);
    const onPlayerStatsChange = this._onPlayerStatsChange.bind(this);
    window.setInterval(onPlayerStatsChange, this.pollingInterval);
    onPlayerStatsChange();
  }

  getPlayerStats(): Promise<PlayerStatsData> {
    return this.fetchStatsService
      .get<PlayerStatsResponse>()
      .then((data) => {
        return { ...data, hasError: false, isReady: true };
      })
      .catch((err) => {
        console.error(err);
        const data: PlayerStatsData = {
          hasError: true,
          isReady: true,
          totalActivePlayers: 0,
        };
        return data;
      });
  }

  _onPlayerStatsChange(/*ev: Event*/) {
    this.getPlayerStats()
      .then((data) => {
        this.data = data;
      })
      .catch((data) => {
        this.data = data;
      })
      .finally(() => {
        this._broadcast();
      });
  }

  _broadcast() {
    this.listeners.forEach((fn /*, id*/) => {
      fn();
    });
  }

  subscribe(fn: PlayerStatsCallback, id: string) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }

  unsubscribe(id: string) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

export const playerStatsService = new PlayerStatsService();
