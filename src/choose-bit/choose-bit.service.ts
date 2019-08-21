export class ChooseBitService {
  constructor() {}

  getBits(limit: number): Promise<string[]> {
    return fetch("/newapi/choose-bit/", {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then(function(response: Response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: any) => {
        return response.data.slice(0, limit);
      });
    });
  }

  claimBit(bit: string): Promise<string | null> {
    const params = new URLSearchParams();
    params.append("icon", bit);
    const request = new Request(`/newapi/claim-bit/?${params}`, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return fetch(request).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }
}

export const chooseBitService = new ChooseBitService();
