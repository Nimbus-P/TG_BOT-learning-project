from typing import Dict, Callable, Any

import requests

from basemodel import BaseSearchAdapter, NOT_RESULT, ERR, NotResult
from config_data.config import API_BASE_URL


def _search_track(message: str, timeout: int = 15):
    if message.strip():
        params = {
            "q": message,
            "limit": 400,
        }
        url = API_BASE_URL + "search"
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    return None


def _top_chart(timeout: int = 15):
    params = {"limit": 500}
    url = API_BASE_URL + "top"
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _convert_result(
    func: Callable, *args, **kwargs
) -> Dict[str, Any] | None | NotResult:
    result_json = func(*args, **kwargs)
    if result_json is not None:
        if result_json["success"]:
            if result_json["count"] > 0:
                data = {"tracks": [], "total_count": result_json["count"]}
                for tracks in result_json["songs"]:
                    track = {
                        "track_id": tracks["rank"],
                        "name": tracks["title"],
                        "artist": tracks["artist"],
                        "audiodownload": tracks["download"],
                    }

                    data["tracks"].append(track)

                return data
            return NOT_RESULT
        raise ERR
    return None


class HitMozAdapter(BaseSearchAdapter):

    @staticmethod
    def _search(
        search_text: str, timeout: int = 15
    ) -> Dict[str, Any] | NotResult | None:
        return _convert_result(func=_search_track, message=search_text, timeout=timeout)

    @staticmethod
    def _top_tracks(timeout: int = 15) -> Dict[str, Any] | NotResult | None:
        return _convert_result(func=_top_chart, timeout=timeout)


if __name__ == "__main__":
    print(_search_track("Камин"))
