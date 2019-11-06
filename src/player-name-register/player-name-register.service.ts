export class PlayerNameRegisterService {
  constructor() {}

  submitName(name: string): Promise<string> {
    const request = new Request(`/newapi/player-name-register/`, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
      }),
    });
    return fetch(request).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }
}
export const playerNameRegisterService = new PlayerNameRegisterService();
