import asyncio
from deep_translator import GoogleTranslator
from utils.parser import ReleaseData
from utils.logger import log

class TranslationService:
    def __init__(self):
        # We instantiate a new translator instance per translation call for thread safety
        pass

    def _translate_sync(self, text: str) -> str:
        if not text or not text.strip():
            return text
            
        try:
            translator = GoogleTranslator(source='ru', target='en')
            return translator.translate(text)
        except Exception as e:
            log.warning(f"action=translation_failed text='{text}' error={e}")
            return text # fallback to original text on failure

    async def translate_text(self, text: str) -> str:
        if not text:
            return text
        return await asyncio.to_thread(self._translate_sync, text)

    async def translate_release(self, release: ReleaseData) -> ReleaseData:
        """Translates the textual fields of a release from Russian to English."""
        log.debug(f"action=translating_release title='{release.title}'")
        
        # Translate fields concurrently if possible, or sequentially. 
        # Sequentially is safer for not getting rate limited by Google.
        title = await self.translate_text(release.title)
        play_via = await self.translate_text(release.play_via)
        modes = await self.translate_text(release.modes)
        categories = await self.translate_text(release.categories)
        
        # Create a new ReleaseData instance to prevent mutating the original 
        # (though namedtuple or dataclass might be used, ReleaseData is a dataclass)
        translated_release = ReleaseData(
            guid=release.guid,
            title=title,
            link=release.link,
            published=release.published,
            image_url=release.image_url,
            release_date=release.release_date, # Date is usually numbers/english
            play_via=play_via,
            modes=modes,
            categories=categories
        )
        
        return translated_release
