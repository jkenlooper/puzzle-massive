class PlayerBitImgService {
  constructor() {}

  getPlayerBitForPlayer(player: number): Promise<string> {
    return fetch(`/chill/site/internal/player-bit/${player}/`, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "text/html",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        return "";
      }
      return response.text();
    });
  }

  /*
  currentUserId(): Promise<string> {
    return fetch("/newapi/current-user-id/", {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }
     */
}

export const playerBitImgService = new PlayerBitImgService();
