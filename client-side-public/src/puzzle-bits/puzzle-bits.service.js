import userDetailsService from "../site/user-details.service";
const BitCacheTimeout = 25 * 60 * 1000; // 25 minutes
const BitRecentTimeout = 5 * 60 * 1000; // 5 minutes in milliseconds
class PuzzleBitsService {
    constructor() {
        this.bits = {};
        this.moveTimeouts = {};
        this.recentTimeouts = {};
        this._bitActiveTimeoutMS = 5 * 1000;
        this._bitRecentTimeoutMS = 60 * 1000;
        this.collection = [];
        this.listeners = new Map();
        const self = this;
        let playerId = userDetailsService.userDetails.id;
        const instanceId = "puzzle-bits.service";
        if (playerId === undefined) {
            userDetailsService.subscribe(() => {
                playerId = userDetailsService.userDetails.id;
                setOwnBit(playerId);
                userDetailsService.unsubscribe(instanceId);
            }, instanceId);
        }
        else {
            setOwnBit(playerId);
        }
        // TODO: set interval to filter out old bits from collection
        window.setInterval(() => {
            const now = new Date();
            this.bits = Object.values(this.bits).reduce((acc, bit) => {
                if (PuzzleBitsService.isRecent(now, bit) || bit.ownBit) {
                    acc[bit.id] = bit;
                }
                return acc;
            }, {});
            self._updateCollection();
            self._broadcast();
        }, BitCacheTimeout);
        self._updateCollection();
        self._broadcast();
        function setOwnBit(playerId) {
            const bit = {
                id: playerId,
                x: 0,
                y: 0,
                lastUpdate: new Date(),
                active: false,
                recent: false,
                ownBit: true,
            };
            if (self.bits[playerId] === undefined) {
                self.bits[playerId] = bit;
            }
            else {
                Object.assign(self.bits[bit.id], bit);
            }
        }
    }
    setBitActiveTimeout(bitActiveTimeout) {
        this._bitActiveTimeoutMS = bitActiveTimeout * 1000;
    }
    setBitRecentTimeout(bitRecentTimeout) {
        this._bitRecentTimeoutMS = bitRecentTimeout * 1000;
    }
    static isRecent(now, bit) {
        return bit.lastUpdate.getTime() > now.getTime() - BitRecentTimeout;
    }
    bitUpdate(data) {
        const self = this;
        const bitId = data.id;
        const bit = Object.assign({
            ownBit: false,
        }, this.bits[bitId] || {}, data, {
            lastUpdate: new Date(),
            active: true,
            recent: true,
        });
        this.moveTimeouts[bitId] = setInactive(bitId);
        this.recentTimeouts[bitId] = setNotRecent(bitId);
        this.bits[bitId] = bit;
        self._updateCollection();
        self._broadcast();
        function setInactive(playerBitId) {
            window.clearTimeout(self.moveTimeouts[playerBitId]);
            return window.setTimeout(() => {
                self.bits[playerBitId].active = false;
                self._updateCollection();
                self._broadcast();
            }, self._bitActiveTimeoutMS);
        }
        function setNotRecent(playerBitId) {
            window.clearTimeout(self.recentTimeouts[playerBitId]);
            return window.setTimeout(() => {
                self.bits[playerBitId].recent = false;
                self._updateCollection();
                self._broadcast();
            }, self._bitRecentTimeoutMS);
        }
    }
    _updateCollection() {
        //const self = this;
        const now = new Date();
        this.collection = Object.values(this.bits).filter((bit) => {
            return PuzzleBitsService.isRecent(now, bit);
        });
    }
    _broadcast() {
        this.listeners.forEach((fn /*, id*/) => {
            fn();
        });
    }
    subscribe(fn, id) {
        // Add the fn to listeners
        this.listeners.set(id, fn);
    }
    unsubscribe(id) {
        // remove fn from listeners
        this.listeners.delete(id);
    }
}
export const puzzleBitsService = new PuzzleBitsService();
