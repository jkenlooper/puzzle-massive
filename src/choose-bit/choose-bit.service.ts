export class ChooseBitService {
  constructor() {}

  getBits(limit: number): Promise<string[]> {
    return fetch("/newapi/choose-bit/").then(function(response: Response) {
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
