import FetchService from "./fetch.service";
class PlayerStatsService {
    constructor() {
        this.listeners = new Map();
        this.pollingInterval = 1 * 60 * 1000; // one minute
        this.data = {
            hasError: false,
            isReady: false,
            totalActivePlayers: 0,
        };
        this.fetchStatsService = new FetchService(`/newapi/player-stats/`);
        const onPlayerStatsChange = this._onPlayerStatsChange.bind(this);
        window.setInterval(onPlayerStatsChange, this.pollingInterval);
        onPlayerStatsChange();
    }
    getPlayerStats() {
        return this.fetchStatsService
            .get()
            .then((data) => {
            return Object.assign(Object.assign({}, data), { hasError: false, isReady: true });
        })
            .catch((err) => {
            console.error(err);
            const data = {
                hasError: true,
                isReady: true,
                totalActivePlayers: 0,
            };
            return data;
        });
    }
    _onPlayerStatsChange( /*ev: Event*/) {
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
    subscribe(fn, id) {
        //console.log("subscribe", fn, id);
        // Add the fn to listeners
        this.listeners.set(id, fn);
    }
    unsubscribe(id) {
        //console.log("unsubscribe", id);
        // remove fn from listeners
        this.listeners.delete(id);
    }
}
export const playerStatsService = new PlayerStatsService();
