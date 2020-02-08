import userDetailsService from "../site/user-details.service";
import { BitMovementData } from "../puzzle-pieces/stream.service";

export interface PlayerBit {
  id: number;
  x: number;
  y: number;
  lastUpdate: Date;
  active: boolean;
  ownBit: boolean;
}
interface PlayerBits {
  [index: number]: PlayerBit;
}
interface MoveTimeouts {
  [playerBitId: number]: number;
}
type PlayerBitsCallback = () => any;

const BitCacheTimeout = 25 * 60 * 1000; // 25 minutes
const BitRecentTimeout = 5 * 60 * 1000; // 5 minutes in milliseconds
const BitActiveTimeout = 5 * 1000; // 5 seconds in milliseconds

class PuzzleBitsService {
  private bits: PlayerBits = {};
  private moveTimeouts: MoveTimeouts = {};
  collection: Array<PlayerBit> = [];
  listeners: Map<string, PlayerBitsCallback> = new Map();

  constructor() {
    const self = this;

    let playerId = userDetailsService.userDetails.id;
    const instanceId = "puzzle-bits.service";
    if (playerId === undefined) {
      userDetailsService.subscribe(() => {
        playerId = <number>userDetailsService.userDetails.id;
        setOwnBit(playerId);
        userDetailsService.unsubscribe(instanceId);
      }, instanceId);
    } else {
      setOwnBit(playerId);
    }

    // TODO: set interval to filter out old bits from collection
    window.setInterval(() => {
      const now = new Date();
      this.bits = <PlayerBits>Object.values(this.bits).reduce((acc, bit) => {
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

    function setOwnBit(playerId: number) {
      const bit: PlayerBit = {
        id: playerId,
        x: 0,
        y: 0,
        lastUpdate: new Date(),
        active: false,
        ownBit: true,
      };
      if (self.bits[playerId] === undefined) {
        self.bits[playerId] = bit;
      } else {
        Object.assign(self.bits[bit.id], bit);
      }
    }
  }

  static isRecent(now: Date, bit: PlayerBit) {
    return bit.lastUpdate.getTime() > now.getTime() - BitRecentTimeout;
  }

  bitUpdate(data: BitMovementData): void {
    const self = this;
    const bitId = data.id;
    const bit: PlayerBit = Object.assign(
      {
        ownBit: false,
      },
      this.bits[bitId] || {},
      data,
      {
        lastUpdate: new Date(),
        active: true,
      }
    );
    this.moveTimeouts[bitId] = setInactive(bitId);

    this.bits[bitId] = bit;

    self._updateCollection();
    self._broadcast();

    function setInactive(playerBitId: number) {
      window.clearTimeout(self.moveTimeouts[playerBitId]);
      return window.setTimeout(() => {
        self.bits[playerBitId].active = false;
        self._updateCollection();
        self._broadcast();
      }, BitActiveTimeout);
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

  subscribe(fn: PlayerBitsCallback, id: string) {
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }

  unsubscribe(id: string) {
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

export const puzzleBitsService = new PuzzleBitsService();
