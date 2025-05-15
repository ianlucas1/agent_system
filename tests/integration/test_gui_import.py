def test_gui_module_importable():
    """Ensure GUI module can be imported without ModuleNotFoundError."""
    __import__("src.interfaces.gui") 