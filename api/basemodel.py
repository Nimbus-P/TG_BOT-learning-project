from abc import ABC, abstractmethod
from typing import Dict, Any, Callable

from utils.logger import logger


class ERR(Exception):
    """Исключение для ошибок API.

    Выбрасывается при неуспешном ответе от API, когда
    headers.status != "success" или headers.code != 0.
    """

    pass


class NotResult:
    """Марк-класс для обозначения пустого результата поиска.

    Используется для отличия ситуации "ничего не найдено"
    от "поиск не выполнялся" (возврат None).
    """

    pass


NOT_RESULT = NotResult()


class Track:
    def __init__(
        self,
        track_id: str,
        name: str,
        artist: str,
        listen_audio: str | None,
        audiodownload: str | None,
    ):
        self.track_id = track_id
        self.name = name
        self.artist = artist
        self.listen_audio = listen_audio
        self.audiodownload = audiodownload


class ResultSearch:
    def __init__(self):
        self.tracks = []
        self.total_count = None
        self.continuation_token = None

    @property
    def tracks_count(self) -> int:
        return len(self.tracks)


class BaseSearchAdapter(ABC):
    @staticmethod
    @abstractmethod
    def _search(*args, **kwargs) -> Dict[str, Any] | NotResult | None:
        pass

    @staticmethod
    def _build_results(data) -> ResultSearch:
        results = ResultSearch()

        for track in data["tracks"]:
            results.tracks.append(
                Track(
                    track_id=str(track["track_id"]),
                    name=track["name"],
                    artist=track["artist"],
                    listen_audio=track.get("listen_audio"),
                    audiodownload=track.get("audiodownload"),
                )
            )

        results.total_count = data.get("total_count")
        results.continuation_token = data.get("continuation_token")

        return results

    @classmethod
    def get_results(
        cls,
        request_func: Callable[..., Dict[str, Any] | NotResult | None],
        *args,
        **kwargs,
    ) -> ResultSearch | NotResult | None:

        result = request_func(*args, **kwargs)

        if isinstance(result, NotResult):
            return NOT_RESULT
        elif result is None:
            logger.warning(
                f"Поиск фактически не выполнялся, например, не переданы параметры."
            )
            return None
        if result:
            return cls._build_results(result)
        return None

