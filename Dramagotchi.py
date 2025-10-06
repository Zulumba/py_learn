#!/usr/bin/env python3
"""Command line and GUI Tamagotchi style pet simulation."""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List

MAX_STAT = 100
MIN_STAT = 0


def clamp(value: int, low: int = MIN_STAT, high: int = MAX_STAT) -> int:
    """Clamp ``value`` so it stays between ``low`` and ``high``."""
    return max(low, min(high, value))


@dataclass
class Tamagotchi:
    name: str
    hunger: int = 65
    happiness: int = 60
    energy: int = 55
    hygiene: int = 70
    last_update: datetime = field(default_factory=datetime.now)

    # Rate in points per minute that each stat naturally decays.
    hunger_decay: int = 4
    happiness_decay: int = 2
    energy_decay: int = 3
    hygiene_decay: int = 1

    def tick(self) -> None:
        """Update the pet according to the time passed since the last update."""
        now = datetime.now()
        elapsed = now - self.last_update
        minutes = elapsed.total_seconds() / 60
        if minutes <= 0:
            return

        def decay(stat: int, rate: int) -> int:
            return clamp(stat - int(minutes * rate))

        self.hunger = decay(self.hunger, self.hunger_decay)
        self.happiness = decay(self.happiness, self.happiness_decay)
        self.energy = decay(self.energy, self.energy_decay)
        self.hygiene = decay(self.hygiene, self.hygiene_decay)
        self.last_update = now

    @property
    def is_alive(self) -> bool:
        return all(
            stat > MIN_STAT
            for stat in (self.hunger, self.happiness, self.energy, self.hygiene)
        )

    def summary(self) -> str:
        bars = {
            "Hunger": self.hunger,
            "Happiness": self.happiness,
            "Energy": self.energy,
            "Hygiene": self.hygiene,
        }
        return "\n".join(
            f"{label:>10}: {value:3d} % |" + "█" * (value // 5) for label, value in bars.items()
        )

    def feed(self) -> str:
        self.tick()
        self.hunger = clamp(self.hunger + 25)
        self.energy = clamp(self.energy + 5)
        self.hygiene = clamp(self.hygiene - 5)
        return "Yummy! " + self._mood_text()

    def play(self) -> str:
        self.tick()
        if self.energy < 15:
            return "Too tired to play right now. Maybe a nap first?"
        self.happiness = clamp(self.happiness + 20)
        self.energy = clamp(self.energy - 15)
        self.hunger = clamp(self.hunger - 10)
        self.hygiene = clamp(self.hygiene - 5)
        return "That was fun! " + self._mood_text()

    def sleep(self) -> str:
        self.tick()
        self.energy = clamp(self.energy + 25)
        self.hunger = clamp(self.hunger - 10)
        return "Zzz... Feeling rested now!"

    def clean(self) -> str:
        self.tick()
        self.hygiene = clamp(self.hygiene + 30)
        self.happiness = clamp(self.happiness - 5)
        return "Splash splash! All squeaky clean."

    def talk(self) -> str:
        self.tick()
        return self._mood_text()

    def _mood_text(self) -> str:
        moods = [
            (self.hunger, "hungry"),
            (self.happiness, "bored"),
            (self.energy, "sleepy"),
            (self.hygiene, "dirty"),
        ]
        needs = [name for value, name in moods if value < 30]
        if not needs:
            return f"{self.name} is feeling great!"
        return f"{self.name} feels a bit {' and '.join(needs)}."


CANONICAL_ACTIONS = [
    "füttern",
    "spielen",
    "schlafen",
    "waschen",
    "reden",
    "status",
    "ende",
]


def available_actions() -> str:
    return "Verfügbare Aktionen: " + ", ".join(CANONICAL_ACTIONS)


@dataclass
class FantasyCharacter:
    """Holds callbacks and metadata for a fantasy themed animation."""

    name: str
    draw: Callable[["TamagotchiAnimation"], None]
    animate: Callable[["TamagotchiAnimation"], None]
    on_game_over: Callable[["TamagotchiAnimation"], None]


def prompt_for_name() -> str:
    while True:
        name = input("Wie soll dein Tamagotchi heißen? ").strip()
        if name:
            return name
        print("Bitte gib einen Namen ein.")


def run_cli() -> None:
    print("🐣 Willkommen zu deinem virtuellen Tamagotchi!")
    pet = Tamagotchi(prompt_for_name())
    actions: Dict[str, Callable[[], str]] = {
        "füttern": pet.feed,
        "futter": pet.feed,
        "feed": pet.feed,
        "spielen": pet.play,
        "play": pet.play,
        "schlafen": pet.sleep,
        "sleep": pet.sleep,
        "waschen": pet.clean,
        "clean": pet.clean,
        "reden": pet.talk,
        "talk": pet.talk,
        "status": pet.summary,
        "hilfe": available_actions,
        "help": available_actions,
        "quit": lambda: "Bis zum nächsten Mal!",
        "ende": lambda: "Bis zum nächsten Mal!",
    }

    print("Tippe 'hilfe' um alle Aktionen zu sehen. Kümmere dich gut um dein Haustier!")

    try:
        while pet.is_alive:
            print("\n" + pet.summary())
            command = input("Was möchtest du tun? ").strip().lower()
            if not command:
                continue
            pet.tick()
            action = actions.get(command)
            if action is None:
                print("Unbekannte Aktion. Tippe 'hilfe' für eine Liste der Befehle.")
                continue
            response = action()
            print(response)
            if command in {"quit", "ende"}:
                break
        else:
            print(f"Oh nein! {pet.name} hat es nicht geschafft. Versuche es noch einmal!")
    except KeyboardInterrupt:
        print("\nBis bald! Dein Tamagotchi wartet auf dich.")


def run_gui() -> None:
    """Startet ein Tkinter-Fenster, um das Tamagotchi visuell zu pflegen."""

    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk

    try:
        name_prompt = tk.Tk()
        name_prompt.withdraw()
    except tk.TclError as exc:
        raise RuntimeError(
            f"Die grafische Oberfläche kann nicht gestartet werden: {exc}"
        ) from exc

    name = ""
    while not name:
        name = simpledialog.askstring(
            "Tamagotchi",
            "Wie soll dein Tamagotchi heißen?",
            parent=name_prompt,
        )
        if name is None:
            name_prompt.destroy()
            return
        name = name.strip()

    name_prompt.destroy()

    class TamagotchiWindow(tk.Tk):
        def __init__(self, pet: Tamagotchi):
            super().__init__()
            self.pet = pet
            self.title(f"{self.pet.name} - Tamagotchi")
            self.resizable(False, False)
            self.configure(padx=20, pady=20)
            self.message_var = tk.StringVar(
                value="Willkommen! Klicke auf eine Aktion, um loszulegen."
            )
            self.stat_labels: Dict[str, tk.StringVar] = {}
            self.progress_bars: Dict[str, ttk.Progressbar] = {}
            self.buttons: Dict[str, ttk.Button] = {}
            self.animation_window = TamagotchiAnimation(self, self.pet)
            self._build_layout()
            self._refresh_stats()
            self._update_loop()
            self.protocol("WM_DELETE_WINDOW", self._on_close)

        def _build_layout(self) -> None:
            heading = tk.Label(
                self,
                text=f"Das ist {self.pet.name}!",
                font=("Helvetica", 16, "bold"),
            )
            heading.grid(row=0, column=0, columnspan=3, pady=(0, 12))

            stat_rows = [
                ("Hunger", "hunger"),
                ("Glück", "happiness"),
                ("Energie", "energy"),
                ("Hygiene", "hygiene"),
            ]

            for row, (label, attribute) in enumerate(stat_rows, start=1):
                tk.Label(self, text=f"{label}:").grid(
                    row=row, column=0, sticky="e", padx=(0, 10)
                )
                progress = ttk.Progressbar(
                    self, orient="horizontal", maximum=MAX_STAT, length=220
                )
                progress.grid(row=row, column=1, sticky="w")
                value_var = tk.StringVar()
                tk.Label(self, textvariable=value_var).grid(
                    row=row, column=2, sticky="w", padx=(10, 0)
                )
                self.progress_bars[attribute] = progress
                self.stat_labels[attribute] = value_var

            message = tk.Label(
                self,
                textvariable=self.message_var,
                wraplength=320,
                justify="center",
                font=("Helvetica", 11),
                pady=12,
            )
            message.grid(row=5, column=0, columnspan=3)

            button_frame = tk.Frame(self)
            button_frame.grid(row=6, column=0, columnspan=3, pady=(0, 5))

            button_specs = [
                ("Füttern", self.pet.feed),
                ("Spielen", self.pet.play),
                ("Schlafen", self.pet.sleep),
                ("Waschen", self.pet.clean),
                ("Reden", self.pet.talk),
                ("Status", self.pet.summary),
            ]

            for index, (text, action) in enumerate(button_specs):
                button = ttk.Button(
                    button_frame,
                    text=text,
                    width=12,
                    command=lambda act=action: self._perform_action(act),
                )
                button.grid(row=index // 3, column=index % 3, padx=6, pady=6)
                self.buttons[text] = button

        def _perform_action(self, action: Callable[[], str]) -> None:
            response = action()
            self.message_var.set(response)
            self._refresh_stats()
            if not self.pet.is_alive:
                self._handle_game_over()

        def _refresh_stats(self) -> None:
            for attribute, progress in self.progress_bars.items():
                value = getattr(self.pet, attribute)
                progress["value"] = value
                self.stat_labels[attribute].set(f"{value:3d} %")

        def _update_loop(self) -> None:
            self.pet.tick()
            self._refresh_stats()
            if self.pet.is_alive:
                self.after(2000, self._update_loop)
            else:
                self._handle_game_over()

        def _handle_game_over(self) -> None:
            for button in self.buttons.values():
                button.configure(state=tk.DISABLED)
            self.message_var.set(
                f"Oh nein! {self.pet.name} hat es nicht geschafft. Starte ein neues Spiel!"
            )
            self.animation_window.on_game_over()
            messagebox.showinfo(
                "Tamagotchi",
                f"Oh nein! {self.pet.name} hat es nicht geschafft. Versuche es noch einmal!",
                parent=self,
            )

        def _on_close(self) -> None:
            self.animation_window.close()
            self.destroy()

    class TamagotchiAnimation(tk.Toplevel):
        def __init__(self, master: tk.Misc, pet: Tamagotchi):
            super().__init__(master)
            self.pet = pet
            self.resizable(False, False)
            self.configure(padx=10, pady=10)

            self.canvas_size = 260
            self.canvas = tk.Canvas(
                self,
                width=self.canvas_size,
                height=self.canvas_size,
                bg="#f0f8ff",
                highlightthickness=0,
            )
            self.canvas.pack()

            self.caption_var = tk.StringVar()
            caption = tk.Label(self, textvariable=self.caption_var, font=("Helvetica", 11, "bold"))
            caption.pack(pady=(8, 0))

            self.character_tag = "fantasy_character"
            self.primary_items: List[int] = []
            self.accent_items: List[int] = []
            self.eye_items: List[int] = []
            self.mouth_id: int | None = None
            self.frame_count = 0

            self.dx = 3
            self.dy = 2
            self.animation_job: int | None = None

            characters = [
                FantasyCharacter(
                    name="Drache",
                    draw=self._draw_dragon,
                    animate=self._animate_dragon,
                    on_game_over=self._dragon_game_over,
                ),
                FantasyCharacter(
                    name="Einhorn",
                    draw=self._draw_unicorn,
                    animate=self._animate_unicorn,
                    on_game_over=self._unicorn_game_over,
                ),
                FantasyCharacter(
                    name="Goblin",
                    draw=self._draw_goblin,
                    animate=self._animate_goblin,
                    on_game_over=self._grey_out_character,
                ),
            ]

            self.character_style = random.choice(characters)
            self.character_style.draw()
            self.title(f"{self.pet.name} als {self.character_style.name}")
            self.caption_var.set(f"Fantastische Form: {self.character_style.name}")

            self.protocol("WM_DELETE_WINDOW", self._on_close)
            self._animate()

        def _reset_character_elements(self) -> None:
            self.canvas.delete(self.character_tag)
            self.primary_items.clear()
            self.accent_items.clear()
            self.eye_items.clear()
            self.mouth_id = None

        def _animate(self) -> None:
            if not self.pet.is_alive:
                self.on_game_over()
                return

            self.frame_count += 1
            self.canvas.move(self.character_tag, self.dx, self.dy)
            self.character_style.animate()

            bbox = self.canvas.bbox(self.character_tag)
            if bbox is not None:
                x1, y1, x2, y2 = bbox
                if x1 <= 0 or x2 >= self.canvas_size:
                    self.dx = -self.dx
                if y1 <= 0 or y2 >= self.canvas_size:
                    self.dy = -self.dy

            self.animation_job = self.after(40, self._animate)

        def _grey_out_character(self) -> None:
            for item in self.primary_items:
                self.canvas.itemconfigure(item, fill="#b0b0b0", outline="#7a7a7a")
            for item in self.accent_items:
                self.canvas.itemconfigure(item, fill="#d3d3d3", outline="#9d9d9d")
            for eye in self.eye_items:
                self.canvas.itemconfigure(eye, fill="#4a4a4a")
            if self.mouth_id is not None:
                self.canvas.itemconfigure(self.mouth_id, extent=180, start=180, outline="#4a4a4a")

        def _dragon_game_over(self) -> None:
            if hasattr(self, "dragon_fire"):
                self.canvas.itemconfigure(self.dragon_fire, state="hidden")
            self._grey_out_character()

        def _unicorn_game_over(self) -> None:
            if hasattr(self, "unicorn_mane_ids"):
                for item in self.unicorn_mane_ids:
                    self.canvas.itemconfigure(item, fill="#d8d8d8")
            if hasattr(self, "unicorn_horn"):
                self.canvas.itemconfigure(self.unicorn_horn, fill="#c0c0c0", outline="#8d8d8d")
            self._grey_out_character()

        def _draw_dragon(self) -> None:
            self._reset_character_elements()
            body = self.canvas.create_oval(
                60,
                120,
                190,
                220,
                fill="#3f7f3f",
                outline="#285028",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(body)

            belly = self.canvas.create_oval(
                105,
                155,
                155,
                220,
                fill="#8bc34a",
                outline="",
                tags=self.character_tag,
            )
            self.accent_items.append(belly)

            head = self.canvas.create_oval(
                150,
                90,
                220,
                150,
                fill="#3f7f3f",
                outline="#285028",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(head)

            tail = self.canvas.create_polygon(
                60,
                190,
                30,
                205,
                70,
                225,
                fill="#3f7f3f",
                outline="#285028",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(tail)

            wing_left = self.canvas.create_polygon(
                90,
                150,
                45,
                110,
                130,
                135,
                fill="#6db170",
                outline="#2f5d2f",
                width=2,
                tags=self.character_tag,
            )
            wing_right = self.canvas.create_polygon(
                165,
                140,
                240,
                110,
                215,
                170,
                fill="#6db170",
                outline="#2f5d2f",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.extend([wing_left, wing_right])
            self.dragon_wings = [wing_left, wing_right]
            self.dragon_wing_direction = 1
            self.dragon_wing_offset = 0

            horn_left = self.canvas.create_polygon(
                165,
                90,
                173,
                60,
                181,
                90,
                fill="#d9b382",
                outline="#b48a58",
                width=2,
                tags=self.character_tag,
            )
            horn_right = self.canvas.create_polygon(
                189,
                92,
                197,
                66,
                205,
                94,
                fill="#d9b382",
                outline="#b48a58",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.extend([horn_left, horn_right])

            eye_left = self.canvas.create_oval(
                175,
                112,
                183,
                120,
                fill="#1d1d1d",
                outline="",
                tags=self.character_tag,
            )
            eye_right = self.canvas.create_oval(
                195,
                112,
                203,
                120,
                fill="#1d1d1d",
                outline="",
                tags=self.character_tag,
            )
            self.eye_items.extend([eye_left, eye_right])

            nostril = self.canvas.create_oval(
                205,
                130,
                212,
                136,
                fill="#285028",
                outline="",
                tags=self.character_tag,
            )
            self.accent_items.append(nostril)

            mouth = self.canvas.create_arc(
                170,
                130,
                210,
                165,
                start=210,
                extent=120,
                style=tk.CHORD,
                outline="#602020",
                width=3,
                tags=self.character_tag,
            )
            self.mouth_id = mouth

            self.dragon_fire = self.canvas.create_polygon(
                215,
                145,
                245,
                160,
                215,
                175,
                fill="#ff8c42",
                outline="#d2691e",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.append(self.dragon_fire)
            self.dragon_fire_visible = True

        def _animate_dragon(self) -> None:
            if not hasattr(self, "dragon_wings"):
                return
            if self.dragon_wing_offset >= 8:
                self.dragon_wing_direction = -1
            elif self.dragon_wing_offset <= -2:
                self.dragon_wing_direction = 1
            for wing in self.dragon_wings:
                self.canvas.move(wing, 0, self.dragon_wing_direction)
            self.dragon_wing_offset += self.dragon_wing_direction

            if self.frame_count % 6 == 0 and hasattr(self, "dragon_fire"):
                self.dragon_fire_visible = not self.dragon_fire_visible
                self.canvas.itemconfigure(
                    self.dragon_fire,
                    state="normal" if self.dragon_fire_visible else "hidden",
                )

        def _draw_unicorn(self) -> None:
            self._reset_character_elements()
            body = self.canvas.create_oval(
                75,
                135,
                205,
                220,
                fill="#f4f0ff",
                outline="#cbb6ff",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(body)

            leg_positions = [(90, 200), (120, 205), (160, 205), (190, 200)]
            self.unicorn_legs: List[int] = []
            for x, y in leg_positions:
                leg = self.canvas.create_rectangle(
                    x,
                    y,
                    x + 12,
                    y + 35,
                    fill="#f4f0ff",
                    outline="#cbb6ff",
                    width=2,
                    tags=self.character_tag,
                )
                hoof = self.canvas.create_rectangle(
                    x,
                    y + 30,
                    x + 12,
                    y + 35,
                    fill="#b8a7ff",
                    outline="#8c7ad1",
                    width=1,
                    tags=self.character_tag,
                )
                self.primary_items.append(leg)
                self.accent_items.append(hoof)
                self.unicorn_legs.append(leg)

            head = self.canvas.create_oval(
                165,
                95,
                225,
                150,
                fill="#f4f0ff",
                outline="#cbb6ff",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(head)

            muzzle = self.canvas.create_oval(
                200,
                120,
                232,
                150,
                fill="#ffe5f1",
                outline="#f0a6ca",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.append(muzzle)

            self.unicorn_mane_palette = ["#d798ff", "#f2a6c7", "#9ad6ff", "#fde68a"]
            mane_positions = [
                (150, 100, 185, 140),
                (135, 115, 170, 155),
                (120, 130, 155, 170),
                (110, 145, 150, 190),
            ]
            self.unicorn_mane_ids = []
            for (x1, y1, x2, y2), color in zip(mane_positions, self.unicorn_mane_palette):
                mane = self.canvas.create_oval(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline="",
                    tags=self.character_tag,
                )
                self.unicorn_mane_ids.append(mane)
                self.accent_items.append(mane)

            tail = self.canvas.create_polygon(
                70,
                175,
                45,
                165,
                55,
                215,
                90,
                210,
                fill="#fde68a",
                outline="#d1aa3d",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.append(tail)

            ear = self.canvas.create_polygon(
                200,
                100,
                210,
                78,
                220,
                102,
                fill="#f4f0ff",
                outline="#cbb6ff",
                width=2,
                tags=self.character_tag,
            )
            self.primary_items.append(ear)

            horn = self.canvas.create_polygon(
                210,
                92,
                220,
                60,
                228,
                95,
                fill="#ffd700",
                outline="#c9a400",
                width=2,
                tags=self.character_tag,
            )
            self.unicorn_horn = horn
            self.accent_items.append(horn)

            eye = self.canvas.create_oval(
                205,
                120,
                213,
                128,
                fill="#3b3b3b",
                outline="",
                tags=self.character_tag,
            )
            self.eye_items.append(eye)

            mouth = self.canvas.create_arc(
                200,
                135,
                230,
                160,
                start=220,
                extent=100,
                style=tk.CHORD,
                outline="#d884b4",
                width=2,
                tags=self.character_tag,
            )
            self.mouth_id = mouth

        def _animate_unicorn(self) -> None:
            if hasattr(self, "unicorn_mane_ids") and self.frame_count % 5 == 0:
                self.unicorn_mane_palette = self.unicorn_mane_palette[1:] + self.unicorn_mane_palette[:1]
                for item, color in zip(self.unicorn_mane_ids, self.unicorn_mane_palette):
                    self.canvas.itemconfigure(item, fill=color)
            if hasattr(self, "unicorn_horn") and self.frame_count % 8 == 0:
                sparkle_color = "#fff4b5" if (self.frame_count // 8) % 2 == 0 else "#ffd700"
                self.canvas.itemconfigure(self.unicorn_horn, fill=sparkle_color)

        def _draw_goblin(self) -> None:
            self._reset_character_elements()
            body = self.canvas.create_oval(
                85,
                130,
                195,
                225,
                fill="#5a9f3a",
                outline="#386427",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(body)

            head = self.canvas.create_oval(
                140,
                85,
                215,
                150,
                fill="#6bbf42",
                outline="#386427",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(head)

            ear_left = self.canvas.create_polygon(
                135,
                110,
                110,
                95,
                130,
                140,
                fill="#6bbf42",
                outline="#386427",
                width=2,
                tags=self.character_tag,
            )
            ear_right = self.canvas.create_polygon(
                215,
                110,
                240,
                95,
                220,
                140,
                fill="#6bbf42",
                outline="#386427",
                width=2,
                tags=self.character_tag,
            )
            self.primary_items.extend([ear_left, ear_right])

            eye_left = self.canvas.create_oval(
                165,
                115,
                173,
                123,
                fill="#1c1c1c",
                outline="",
                tags=self.character_tag,
            )
            eye_right = self.canvas.create_oval(
                187,
                115,
                195,
                123,
                fill="#1c1c1c",
                outline="",
                tags=self.character_tag,
            )
            self.eye_items.extend([eye_left, eye_right])

            tusk = self.canvas.create_polygon(
                195,
                135,
                205,
                145,
                195,
                150,
                fill="#f8f0d2",
                outline="#c5b890",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.append(tusk)

            mouth = self.canvas.create_arc(
                160,
                135,
                200,
                165,
                start=200,
                extent=130,
                style=tk.CHORD,
                outline="#2d4d1d",
                width=3,
                tags=self.character_tag,
            )
            self.mouth_id = mouth

            arm = self.canvas.create_polygon(
                120,
                160,
                95,
                190,
                130,
                195,
                140,
                170,
                fill="#5a9f3a",
                outline="#386427",
                width=3,
                tags=self.character_tag,
            )
            self.primary_items.append(arm)

            club = self.canvas.create_polygon(
                90,
                195,
                75,
                240,
                105,
                245,
                120,
                205,
                fill="#8b5a2b",
                outline="#5a3517",
                width=2,
                tags=self.character_tag,
            )
            self.goblin_club = club
            self.accent_items.append(club)
            self.goblin_club_direction = 1
            self.goblin_club_offset = 0

            belt = self.canvas.create_rectangle(
                105,
                190,
                175,
                205,
                fill="#2d4d1d",
                outline="#172a0f",
                width=2,
                tags=self.character_tag,
            )
            self.accent_items.append(belt)

            feet = self.canvas.create_rectangle(
                120,
                220,
                185,
                235,
                fill="#386427",
                outline="#1f2d15",
                width=2,
                tags=self.character_tag,
            )
            self.primary_items.append(feet)

        def _animate_goblin(self) -> None:
            if not hasattr(self, "goblin_club"):
                return
            if self.goblin_club_offset >= 8:
                self.goblin_club_direction = -1
            elif self.goblin_club_offset <= -2:
                self.goblin_club_direction = 1
            self.canvas.move(self.goblin_club, 0, self.goblin_club_direction)
            self.goblin_club_offset += self.goblin_club_direction

        def on_game_over(self) -> None:
            if self.animation_job is not None:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            self.character_style.on_game_over()

        def close(self) -> None:
            if self.animation_job is not None:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            self.destroy()

        def _on_close(self) -> None:
            # Withdraw instead of destroying to avoid orphaning references in the main window
            self.withdraw()

    TamagotchiWindow(Tamagotchi(name)).mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtuelles Tamagotchi pflegen.")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Starte den Textmodus statt der grafischen Oberfläche",
    )
    args = parser.parse_args()

    if args.cli:
        run_cli()
        return

    try:
        run_gui()
    except RuntimeError as exc:
        print(f"{exc}. Wechsle in den Textmodus...")
        run_cli()


if __name__ == "__main__":
    main()