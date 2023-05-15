#! /usr/bin/python3

from appdata import AppDataPaths
import db, algorithm
import random
import sys
import subprocess, os, platform
import zipfile
import logging
import shutil
from datetime import datetime, timedelta


from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolButton, QLabel, QMenu, QTreeView, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QInputDialog, QMessageBox, QFileDialog, QAbstractItemView
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont, QAction

app = QApplication(sys.argv)
app_paths = AppDataPaths("repetition")


'''
This file is main entry point of the application and handles most of the GUI stuff

@author: David Buehler
@date: January/February/March 2023
'''


class MainWindow(QWidget):
    current_card = None
    active_deck = None
    due_cards = None

    stackedWidget = QStackedWidget()

    study_page = {
        "title_label": None,
        "created_at_label": None,
        "btn_open_file": None
    }
    deck_list = None

    card_list = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Repetition - All Decks')
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_page = QWidget()
        main_page.setLayout(self.create_main_layout(self.get_deck_item_model()))
        self.stackedWidget.addWidget(main_page)
        study_page = QWidget()
        study_page.setLayout(self.create_study_layout())
        self.stackedWidget.addWidget(study_page)
        edit_page = QWidget()
        edit_page.setLayout(self.create_edit_layout())
        self.stackedWidget.addWidget(edit_page)
        main_layout.addWidget(self.stackedWidget)
        self.show()

    @staticmethod
    def get_deck_item_model():
        print("[I] Scanning for decks")
        decks = db.get_decks()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Decks'])
        root_item = model.invisibleRootItem()

        items = dict()

        bold_font = QFont()
        bold_font.setBold(True)

        for deck in decks:
            print(f"[D] Found deck: {deck['name']}")
            item = QStandardItem(deck['name'])
            if len(db.get_cards(deck['name'], only_due=True)) == 0:
                item.setEditable(False)
            else:
                item.setFont(bold_font)
            items[deck["name"]] = item

        for deck in decks:
            if deck["parent"] == None:
                root_item.appendRow(items[deck["name"]])
            else:
                items[deck["parent"]].appendRow(items[deck["name"]])
        return model

    def get_cards_item_model(self, deck):
        cards = db.get_cards(deck, include_children_cards=False, only_due=False)
        model = QStandardItemModel()
        model.dataChanged.connect(self.on_card_renamed)
        model.setHorizontalHeaderLabels(['Cards'])
        root_item = model.invisibleRootItem()

        for card in cards:
            item = QStandardItem(card['title'])
            item.setData(card['title'], Qt.ItemDataRole.DisplayRole.UserRole)
            root_item.appendRow(item)
        return model

    def create_main_layout(self, model):
        # Create a vertical layout to hold the horizontal layout and the tree view
        layout = QVBoxLayout()

        # Create a horizontal layout to hold the buttons
        button_layout = QHBoxLayout()

        button_layout.addStretch()

        btn_createDeck = QPushButton('Create Deck')
        btn_createDeck.clicked.connect(self.create_deck)
        button_layout.addWidget(btn_createDeck)

        btn_editDeck = QPushButton()
        btn_editDeck.setText('Edit Deck')
        btn_editDeck.clicked.connect(self.on_edit_deck_clicked)
        button_layout.addWidget(btn_editDeck)

        btn_createCard = QPushButton('Create Card')
        btn_createCard.clicked.connect(self.create_card)
        button_layout.addWidget(btn_createCard)

        btn_import = QPushButton('Import')
        btn_import.clicked.connect(self.import_from_file)
        button_layout.addWidget(btn_import)

        btn_export = QPushButton('Export')
        btn_export.clicked.connect(self.export)
        button_layout.addWidget(btn_export)

        button_layout.addStretch()

        # Add the horizontal layout to the vertical layout
        layout.addLayout(button_layout)

        # Create a tree view and add it to the vertical layout
        tree_view = DeckView(self)
        tree_view.setModel(model)
        self.deck_list = tree_view
        layout.addWidget(tree_view)
        return layout

    def create_study_layout(self):
        layout = QVBoxLayout()
        title_label = QLabel("title")
        title_label.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        self.study_page["title_label"] = title_label
        layout.addWidget(title_label)
        created_at_label = QLabel('Created at {created_at}')
        self.study_page["created_at_label"] = created_at_label
        layout.addWidget(created_at_label)
        layout.addStretch()

        # Above the difficulty buttons, there's a row with "management buttons"
        management_layout = QHBoxLayout()
        management_layout.addStretch()
        btn_open = QPushButton('Open Attached File')
        btn_open.clicked.connect(self.on_file_open_clicked)
        self.study_page["btn_open_file"] = btn_open
        management_layout.addWidget(btn_open)
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.return_to_main_screen)
        management_layout.addWidget(btn_cancel)
        management_layout.addStretch()
        management_layout.setAlignment(self, QtCore.Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(management_layout)

        # Create a horizontal layout to hold the difficulty buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        btn_again = QPushButton('Forgot')
        btn_again.clicked.connect(lambda: self.on_difficulty_button_clicked(1))
        button_layout.addWidget(btn_again)
        btn_hard = QPushButton('Hard')
        btn_hard.clicked.connect(lambda: self.on_difficulty_button_clicked(2))
        button_layout.addWidget(btn_hard)
        btn_good = QPushButton('Good')
        btn_good.clicked.connect(lambda: self.on_difficulty_button_clicked(3))
        button_layout.addWidget(btn_good)
        btn_easy = QPushButton('Easy')
        btn_easy.clicked.connect(lambda: self.on_difficulty_button_clicked(4))
        button_layout.addWidget(btn_easy)
        button_layout.addStretch()
        button_layout.setAlignment(self, QtCore.Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(button_layout)
        return layout

    def create_edit_layout(self):
        layout = QVBoxLayout()
        management_layout = QHBoxLayout()
        management_layout.addStretch()
        btn_back = QPushButton('← Back')
        btn_back.clicked.connect(self.return_to_main_screen)
        management_layout.addWidget(btn_back)
        btn_delete_deck = QPushButton('Delete Deck')
        btn_delete_deck.clicked.connect(self.on_delete_deck_clicked)
        management_layout.addWidget(btn_delete_deck)
        btn_rename_deck = QPushButton('Rename Deck')
        btn_rename_deck.clicked.connect(self.on_rename_deck_clicked)
        management_layout.addWidget(btn_rename_deck)
        btn_delete_card = QPushButton('Delete Card')
        btn_delete_card.clicked.connect(self.on_delete_card_clicked)
        management_layout.addWidget(btn_delete_card)
        management_layout.addStretch()
        layout.addLayout(management_layout)

        self.card_list = QTreeView()
        layout.addWidget(self.card_list)
        return layout

    def update_study_layout(self):
        self.study_page["title_label"].setText(self.current_card["title"])
        self.study_page["created_at_label"].setText(f"Created at {self.current_card['created_at']}")
        self.study_page["btn_open_file"].setEnabled(self.current_card["filename"] is not None)

    # Click actions
    def on_file_open_clicked(self):
        filepath = os.path.join(db.app_paths.app_data_path, self.current_card["filename"])
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filepath))

    @staticmethod
    def export():
        zip_file_name, _ = QFileDialog.getSaveFileName(None, "Save Zip File", "", "Zip Files (*.zip)")
        if zip_file_name:
            print(f"[D] Selected file path: {zip_file_name}")
            with zipfile.ZipFile(zip_file_name, "w") as zip_archive:
                # Iterate through the files in the directory
                for file_name in os.listdir(app_paths.app_data_path):
                    if file_name not in ["locks", "logs"]:
                        # Construct the full path to the file
                        file_path = os.path.join(app_paths.app_data_path, file_name)
                        # Add the file to the zip archive
                        zip_archive.write(file_path, arcname=file_name)
                    else:
                        print(f"[D] {file_name} was ignored and not added to the archive")

            print(f"Files added to {zip_file_name} successfully!")

    def import_from_file(self):
        msg_box = QMessageBox()
        msg_box.setText("This will replace all your decks and cards with the imported archive. Continue?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Yes:
            zip_file_name, ok = QFileDialog.getOpenFileName(None, "Choose file", "", "Zip Files (*.zip)")
            if ok and zip_file_name:
                try:
                    with zipfile.ZipFile(zip_file_name, "r") as zip_archive:
                        if "cards.db" in zip_archive.namelist():
                            db.close()
                            # extract the archive
                            zip_archive.extractall(app_paths.app_data_path)
                            # re-open the connection
                            db.connect_DB()
                            # update layout
                            self.deck_list.setModel(self.get_deck_item_model())
                            QMessageBox.information(None, "Information", "Import successful.")
                        else:
                            QMessageBox.critical(None, "Error", "Selected archive is not valid.\nReason: Missing database")
                except zipfile.BadZipFile as e:
                    QMessageBox.critical(None, "Error", f"Import failed.\nReason: {e}")

    def on_edit_deck_clicked(self):
        deck = self.deck_list.model().data(self.deck_list.currentIndex(), QtCore.Qt.ItemDataRole.DisplayRole)
        if deck is None:
            QMessageBox.critical(None, "Error", "Select a deck first to proceed.")
            return
        print(f"[I] Editing {deck}")
        self.active_deck = deck
        self.setWindowTitle(f"Repetition - Editing {deck}")
        self.stackedWidget.setCurrentIndex(2)
        self.update_edit_layout()

    def update_edit_layout(self):
        self.card_list.setModel(self.get_cards_item_model(self.active_deck))

    def on_delete_deck_clicked(self):
        msg_box = QMessageBox()
        msg_box.setText("Are you sure? This will delete all sub-decks as well.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # execute the message box and get the result
        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Yes:
            db.delete_deck(self.active_deck)
            self.return_to_main_screen()

    def on_rename_deck_clicked(self):
        new_name, ok = QInputDialog.getText(None, 'Enter new Name', 'Enter the new name:', text=self.active_deck)

        if ok and new_name:
            print(f"[I] deck {self.active_deck} was renamed to {new_name}")
            db.rename_deck(self.active_deck, new_name)
            self.active_deck = new_name
            self.setWindowTitle(f"Repetition - Editing {self.active_deck}")
            self.update_edit_layout()

    def on_delete_card_clicked(self):
        card = self.card_list.model().data(self.card_list.currentIndex(), QtCore.Qt.ItemDataRole.DisplayRole)
        if card is None:
            QMessageBox.critical(None, "Error", "Select a card first to proceed.")
            return

        msg_box = QMessageBox()
        msg_box.setText("Are you sure?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # execute the message box and get the result
        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Yes:
            db.delete_card(card)
            self.update_edit_layout()

    def on_card_renamed(self, index):
        if index.column() == 0 and index.data(Qt.DisplayRole):
            item = self.card_list.model().itemFromIndex(index)
            new_name = item.text()
            previous_name = item.data(Qt.ItemDataRole.DisplayRole.UserRole)

            print(f"[I] Item {previous_name} was renamed to {new_name}")
            if not db.rename_card(previous_name, new_name):
                QMessageBox.critical(None, "Error", "Couldn't rename card. Most likely, a card with that name already exists.")
            self.update_edit_layout()

    def create_deck(self):
        name, ok = QInputDialog.getText(self, 'Enter Name', "Enter the deck's name:")
        if ok and name:
            if not db.add_deck(name):
                QMessageBox.critical(None, "Error", "A deck with that name already exists.")
            else:
                # Update deck list
                self.deck_list.setModel(self.get_deck_item_model())

    def create_card(self):
        deck = self.deck_list.model().data(self.deck_list.currentIndex(), QtCore.Qt.ItemDataRole.DisplayRole)
        if deck is None:
            QMessageBox.critical(None, "Error", "Select a deck first to proceed.")
            return
        print(f"[I] Adding card to {deck}")
        title, ok = QInputDialog.getText(self, f'Add to {deck}', "Enter the card's title:")
        if ok and title:
            msg_box = QMessageBox()
            msg_box.setText("Do you want to attach a file?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            # execute the message box and get the result
            result = msg_box.exec()
            file_name, source_file, dest_file = None, None, None
            if result == QMessageBox.StandardButton.Yes:
                file_dialog = QFileDialog()
                source_file, ok = file_dialog.getOpenFileName(window, "Choose file", "", "All Files (*)")

                if ok and source_file:
                    # import file
                    # to make it possible for two files to have the same name,
                    # the file name is prepended with the hash of the card's
                    # title.
                    file_name = str(hash(title)) + "_" + os.path.basename(source_file)
                    dest_file = os.path.join(app_paths.app_data_path, file_name)
            if not db.add_card(deck, title, file_name):
                QMessageBox.critical(None, "Error", "A card with that title already exists.")
            else:
                if dest_file is not None:
                    print(f"[I] Importing {file_name}")
                    # Import the file. Only import it now since importing it with an already existing card could
                    # lead to the card's file being overwritten, if the new file has the same file name
                    shutil.copy2(source_file, dest_file)
                # Update deck list
                self.deck_list.setModel(self.get_deck_item_model())

    def study(self, deck):
        self.active_deck = deck
        print(f"[I] Studying {self.active_deck}")
        self.due_cards = db.get_cards(self.active_deck, only_due=True)
        print(f"[I] There are {len(self.due_cards)} due cards in this deck")
        random.shuffle(self.due_cards)
        if self.due_cards:
            self.setWindowTitle(f'Repetition - {self.active_deck}')
            # get the first card
            self.current_card = self.due_cards[0]
            # and remove it from the queue
            self.due_cards.remove(self.current_card)

            self.update_study_layout()

            self.stackedWidget.setCurrentIndex(1)
        else:
            QMessageBox.information(None, "Information", "This deck does not have any due cards.")

    def return_to_main_screen(self):
        self.setWindowTitle('Repetition - All Decks')
        # refresh decks
        self.deck_list.setModel(self.get_deck_item_model())
        # show main screen
        self.stackedWidget.setCurrentIndex(0)

    def next_card(self):
        if self.due_cards is not None and len(self.due_cards) > 0:
            print(f"[I] There are {len(self.due_cards)} cards left to study")
            self.current_card = self.due_cards[0]
            self.due_cards.remove(self.current_card)
            self.update_study_layout()
        else:
            print("[I] No due cards left")
            self.return_to_main_screen()

    def on_difficulty_button_clicked(self, grade):
        # get the necessary parameters
        s_i = self.current_card["last_interval"] or 0
        next_due_date = datetime.strptime(self.current_card["next_due_date"], "%Y-%m-%d")
        # the card was last studied at due date - last stability
        delta_t = (datetime.today().date() - (next_due_date.date() - timedelta(days=s_i))).days
        d_i = self.current_card["last_difficulty"]
        new_card = d_i is None

        print(f"[D] delta_t = {delta_t}")

        # Run algorithm
        stability, difficulty = algorithm.calculate_stability_difficulty(s_i, delta_t, d_i, grade, new_card)

        # Debug prints
        print(f"[D] algorithm returned: d_i+1 = {difficulty}, s_i+1 = {stability}")

        # Update values
        next_due_date = next_due_date.date() + timedelta(days=stability)
        db.update_card_after_review(self.current_card["title"], difficulty, stability, next_due_date)

        print(f"[I] DB updated, card is due again at {next_due_date}")

        self.next_card()


class DeckView(QTreeView):
    main_window = None

    def __init__(self, main_window, parent=None):
        super().__init__(parent)

        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dropEvent(self, event):
        print("[D] Handling drop event")

        fake_model = QStandardItemModel()
        fake_model.dropMimeData(
            event.mimeData(), event.dropAction(), 0, 0, QtCore.QModelIndex()
        )
        child = fake_model.index(0, 0).data()
        to_index = self.indexAt(event.position().toPoint())
        if to_index.isValid():
            if to_index.data() == child:
                print("[I] deck droppped onto itself, no change performed")
                super().dropEvent(event)
                return
            # parent is a deck
            print(f"[I] Changing parent of {child} to {to_index.data()}")
            db.change_deck_parent(child, to_index.data())
        else:
            # no parent - dropped into the void
            print(f"[I] Setting parent of {child} to NULL")
            db.change_deck_parent(child)

        super().dropEvent(event)
        # Currently, a re-ordering is also considered as a drop onto a deck
        # To reflect that on the UI, update it
        self.setModel(self.main_window.get_deck_item_model())

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            print("[D] Double-clicked on item at", index.row())
            self.main_window.study(self.model().data(index, QtCore.Qt.ItemDataRole.DisplayRole))

        else:
            super().mouseDoubleClickEvent(event)


class LogWriter:
    @staticmethod
    def write(message):
        logging.info(message.strip())

    def flush(self):
        pass


if __name__ == '__main__':
    if app_paths.require_setup:
        app_paths.setup()

    logging.basicConfig(filename=app_paths.log_file_path, level=logging.DEBUG)
    logging.info(f"New Application startup at {datetime.now()}")
    sys.stdout = LogWriter()
    sys.stderr = LogWriter()

    db.connect_DB()

    window = MainWindow()
    window.resize(600, 500)
    print("[D] Main window initialised")
    print("[D] calling app.exec")
    sys.exit(app.exec())
