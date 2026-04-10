"""Tests for frontend.upload_tab."""

import os

import frontend.upload_tab as upload_tab


class DummyVar:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class DummyListbox:
    def __init__(self, values=None, selection=()):
        self.values = list(values or [])
        self.selection = tuple(selection)

    def curselection(self):
        return self.selection

    def get(self, index):
        return self.values[index]

    def delete(self, _start, _end=None):
        self.values = []

    def insert(self, _where, value):
        self.values.append(value)


def test_on_select_sets_selected_path(monkeypatch):
    tab = upload_tab.UploadTab.__new__(upload_tab.UploadTab)
    tab.listbox = DummyListbox(values=["banner.png"], selection=(0,))
    tab._path_var = DummyVar("")
    monkeypatch.setattr(upload_tab, "UPLOADS_DIR", "uploads")

    upload_tab.UploadTab._on_select(tab)
    assert tab._path_var.get() == os.path.join("uploads", "banner.png")


def test_refresh_populates_listbox(monkeypatch):
    tab = upload_tab.UploadTab.__new__(upload_tab.UploadTab)
    tab.listbox = DummyListbox(values=["old.png"])
    tab._path_var = DummyVar("x")
    monkeypatch.setattr(
        upload_tab, "list_uploaded_files", lambda: [{"name": "a.png"}, "b.png"]
    )

    upload_tab.UploadTab._refresh(tab)

    assert tab.listbox.values == ["a.png", "b.png"]
    assert tab._path_var.get() == ""


def test_remove_with_no_selection_shows_warning(monkeypatch):
    warns = []
    tab = upload_tab.UploadTab.__new__(upload_tab.UploadTab)
    tab.listbox = DummyListbox(values=["a.png"], selection=())
    tab._refresh = lambda: None
    monkeypatch.setattr(
        upload_tab.messagebox,
        "showwarning",
        lambda title, msg: warns.append((title, msg)),
    )

    upload_tab.UploadTab._remove(tab)
    assert warns == [("Remove File", "No file selected.")]


def test_remove_selected_success(monkeypatch):
    infos = []
    tab = upload_tab.UploadTab.__new__(upload_tab.UploadTab)
    tab.listbox = DummyListbox(values=["a.png"], selection=(0,))
    refresh_called = {"value": 0}
    tab._refresh = lambda: refresh_called.__setitem__(
        "value", refresh_called["value"] + 1
    )

    monkeypatch.setattr(upload_tab, "delete_upload", lambda name: name == "a.png")
    monkeypatch.setattr(
        upload_tab.messagebox, "showinfo", lambda title, msg: infos.append((title, msg))
    )

    upload_tab.UploadTab._remove(tab)

    assert infos == [("Remove", "Deleted: a.png")]
    assert refresh_called["value"] == 1


def test_choose_uploads_valid_and_reports_invalid(monkeypatch):
    infos = []
    errors = []
    saved = []
    refreshed = {"value": 0}

    tab = upload_tab.UploadTab.__new__(upload_tab.UploadTab)
    tab._refresh = lambda: refreshed.__setitem__("value", refreshed["value"] + 1)

    monkeypatch.setattr(
        upload_tab.filedialog,
        "askopenfilenames",
        lambda title, filetypes: ["C:/x/ok.png", "C:/x/bad.txt"],
    )
    monkeypatch.setattr(upload_tab, "allowed_file", lambda name: name.endswith(".png"))
    monkeypatch.setattr(
        upload_tab,
        "save_upload",
        lambda path: saved.append(path) or ("uploads/" + path.split("/")[-1]),
    )
    monkeypatch.setattr(
        upload_tab.messagebox, "showinfo", lambda title, msg: infos.append((title, msg))
    )
    monkeypatch.setattr(
        upload_tab.messagebox,
        "showerror",
        lambda title, msg: errors.append((title, msg)),
    )

    upload_tab.UploadTab._choose(tab)

    assert saved == ["C:/x/ok.png"]
    assert infos == [("Upload", "Saved 1 file(s).")]
    assert errors == [("Upload", "Skipped 1 unsupported file(s):\nbad.txt")]
    assert refreshed["value"] == 1
