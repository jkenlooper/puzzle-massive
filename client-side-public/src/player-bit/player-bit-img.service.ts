interface PlayerBits {
  [playerId: number]: string | Promise<string>;
}

// Golden Ratio Conjugate
const GRC = 0.6180339887;

export function colorForPlayer(player) {
  const hue = ((player * GRC) % 1) * 360;
  const sat = 85 + Math.round(Math.abs(Math.sin(player)) * 15);
  const lit = 25 + Math.round(Math.abs(Math.sin(player)) * 10);
  return `hsl(${hue}, ${sat}%, ${lit}%)`;
}

const _playerBits: PlayerBits = {};

class PlayerBitImgService {
  constructor() {}

  getPlayerBitForPlayer(player: number): Promise<string> {
    if (_playerBits[player]) {
      return Promise.resolve(_playerBits[player]);
    } else {
      const defer = fetch(`/chill/site/internal/player-bit/${player}/`, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          "Content-Type": "text/html",
        },
      })
        .then((response: Response) => {
          if (response.ok) {
            return response.text();
          }
          return Promise.resolve("");
        })
        .then((playerBit: string) => {
          _playerBits[player] = playerBit;
          return playerBit;
        });
      _playerBits[player] = defer;
      return defer;
    }
  }
}

export const playerBitImgService = new PlayerBitImgService();
