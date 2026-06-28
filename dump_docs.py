import discord.ui as ui
import inspect

classes = [ui.LayoutView, ui.Container, ui.Section, ui.TextDisplay, ui.MediaGallery, ui.Separator]

with open('docs_dump.txt', 'w') as f:
    for cls in classes:
        try:
            f.write(f"=== {cls.__name__} ===\n")
            f.write(inspect.getdoc(cls) or "No doc")
            f.write("\n\nMethods:\n")
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                f.write(f"  {name}{inspect.signature(method)}\n")
            f.write("\n\n")
        except Exception as e:
            f.write(f"Error on {cls}: {e}\n\n")
