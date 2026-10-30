"""Online Mock Test - Kivy version of the HTML exam page.

Features: timer, question palette, mark for review, clear response,
save & next, negative marking, result page, answer review,
keyboard shortcuts (A/B/C/D, arrows, Enter) for desktop testing.
"""
import json
import os
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.utils import escape_markup

# ---------------------------------------------------------------- settings
TOTAL_SECONDS = 60 * 60      # test duration (same as the HTML: 60 * 60)
NEGATIVE_MARK = True
NEGATIVE_VALUE = 0.33

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansBengali-Regular.ttf")

# Bengali needs a Bengali-capable font. Replace the default font globally.
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH, fn_bold=FONT_PATH)

# palette colours (same meaning as the HTML)
C_NOT_VISITED = (0, 0, 0, 1)
C_NOT_ANSWERED = (1, 1, 1, 1)
C_ANSWERED = (0, 0.5, 0, 1)
C_REVIEW = (0.5, 0, 0.5, 1)
C_ANS_REVIEW = (1, 0.65, 0, 1)
C_BLUE = (0, 0.4, 1, 1)
C_RED = (0.85, 0.1, 0.1, 1)
C_TOPBAR = (0.21, 0.34, 0.4, 1)
BG = (0.95, 0.96, 0.97, 1)


def load_questions():
    with open(os.path.join(BASE_DIR, "questions.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- widgets
class WrapLabel(Label):
    """Label that wraps text to its width and grows in height."""

    def __init__(self, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("halign", "left")
        kw.setdefault("valign", "top")
        kw.setdefault("color", (0.1, 0.1, 0.1, 1))
        kw.setdefault("markup", False)
        super().__init__(**kw)
        self.bind(width=self._on_width, texture_size=self._on_tex)

    def _on_width(self, *_):
        self.text_size = (self.width, None)

    def _on_tex(self, *_):
        self.height = self.texture_size[1] + dp(12)


class Btn(Button):
    def __init__(self, bg=C_BLUE, fg=(1, 1, 1, 1), **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("font_size", sp(14))
        super().__init__(**kw)
        self.background_color = bg
        self.color = fg


class OptionButton(Button):
    def __init__(self, selected=False, **kw):
        super().__init__(
            background_normal="", background_down="",
            halign="left", valign="middle", size_hint_y=None,
            font_size=sp(15), color=(0, 0, 0, 1), **kw)
        self.background_color = (0.75, 0.88, 1, 1) if selected else (0.93, 0.93, 0.93, 1)
        self.bind(width=self._on_width, texture_size=self._on_tex)

    def _on_width(self, *_):
        self.text_size = (self.width - dp(24), None)

    def _on_tex(self, *_):
        self.height = max(dp(48), self.texture_size[1] + dp(24))


def make_scroll_column(**kw):
    """Return (ScrollView, BoxLayout) where the box grows with its content."""
    sv = ScrollView(do_scroll_x=False, **kw)
    box = BoxLayout(orientation="vertical", size_hint_y=None,
                    padding=dp(10), spacing=dp(8))
    box.bind(minimum_height=box.setter("height"))
    sv.add_widget(box)
    return sv, box


def confirm_dialog(text, on_yes):
    view = ModalView(size_hint=(0.85, None), height=dp(190), auto_dismiss=False)
    root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
    root.add_widget(Label(text=text, color=(1, 1, 1, 1), font_size=sp(16)))
    row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    no = Btn(text="No", bg=(0.4, 0.4, 0.4, 1))
    yes = Btn(text="Yes", bg=C_RED)
    no.bind(on_release=lambda *_: view.dismiss())
    yes.bind(on_release=lambda *_: (view.dismiss(), on_yes()))
    row.add_widget(no)
    row.add_widget(yes)
    root.add_widget(row)
    view.add_widget(root)
    view.open()


# ---------------------------------------------------------------- screens
class StartScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="start", **kw)
        self.app_ = app
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        root.add_widget(Label(size_hint_y=0.2))
        root.add_widget(Label(text="Online Mock Test", font_size=sp(28),
                              color=(0.1, 0.1, 0.1, 1), size_hint_y=None,
                              height=dp(60)))
        self.info = Label(color=(0.1, 0.1, 0.1, 1), font_size=sp(17),
                          halign="center")
        root.add_widget(self.info)
        btn = Btn(text="Start Test", size_hint_y=None, height=dp(52),
                  font_size=sp(18))
        btn.bind(on_release=lambda *_: app.start_test())
        root.add_widget(btn)
        root.add_widget(Label(size_hint_y=0.2))
        self.add_widget(root)

    def on_pre_enter(self, *_):
        n = len(self.app_.questions)
        self.info.text = (
            f"Total Questions: {n}\n"
            f"Time: {TOTAL_SECONDS // 60} Minutes\n"
            f"Negative Marking: {'ON' if NEGATIVE_MARK else 'OFF'}"
        )


class ExamScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="exam", **kw)
        self.app_ = app
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        # top bar
        top = BoxLayout(size_hint_y=None, height=dp(46), padding=dp(8))
        from kivy.graphics import Color, Rectangle
        with top.canvas.before:
            Color(*C_TOPBAR)
            self._rect = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda w, v: setattr(self._rect, "pos", v),
                 size=lambda w, v: setattr(self._rect, "size", v))
        self.timer_lbl = Label(text="--:--", color=(1, 0.8, 0, 1),
                               font_size=sp(16), bold=True)
        self.qno_lbl = Label(text="", color=(1, 1, 1, 1), font_size=sp(16))
        top.add_widget(self.timer_lbl)
        top.add_widget(self.qno_lbl)
        root.add_widget(top)

        # question + options
        self.scroll, self.box = make_scroll_column()
        root.add_widget(self.scroll)

        # buttons row 1
        r1 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        self.b_prev = Btn(text="Previous")
        self.b_clear = Btn(text="Clear", bg=(0.4, 0.4, 0.4, 1))
        self.b_mark = Btn(text="Mark Review", bg=C_REVIEW)
        self.b_save = Btn(text="Save & Next", bg=C_ANSWERED)
        self.b_prev.bind(on_release=lambda *_: app.go_prev())
        self.b_clear.bind(on_release=lambda *_: app.clear_answer())
        self.b_mark.bind(on_release=lambda *_: app.toggle_review())
        self.b_save.bind(on_release=lambda *_: app.go_next())
        for b in (self.b_prev, self.b_clear, self.b_mark, self.b_save):
            r1.add_widget(b)
        root.add_widget(r1)

        # buttons row 2
        r2 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        b_pal = Btn(text="Question Palette", bg=(0.1, 0.1, 0.1, 1))
        b_sub = Btn(text="Submit Test", bg=C_RED)
        b_pal.bind(on_release=lambda *_: app.open_palette())
        b_sub.bind(on_release=lambda *_: app.ask_submit())
        r2.add_widget(b_pal)
        r2.add_widget(b_sub)
        root.add_widget(r2)

        self.add_widget(root)


class ResultScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="result", **kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        root.add_widget(Label(text="Test Result", font_size=sp(26),
                              color=(0.1, 0.1, 0.1, 1), size_hint_y=None,
                              height=dp(60)))
        self.result_lbl = Label(color=(0.1, 0.1, 0.1, 1), font_size=sp(18),
                                halign="center")
        root.add_widget(self.result_lbl)
        b1 = Btn(text="Review Answers", size_hint_y=None, height=dp(50))
        b2 = Btn(text="New Test", bg=(0.4, 0.4, 0.4, 1),
                 size_hint_y=None, height=dp(50))
        b1.bind(on_release=lambda *_: app.show_review())
        b2.bind(on_release=lambda *_: app.new_test())
        root.add_widget(b1)
        root.add_widget(b2)
        self.add_widget(root)


class ReviewScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(name="review", **kw)
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        root.add_widget(Label(text="Answer Review", font_size=sp(22),
                              color=(0.1, 0.1, 0.1, 1), size_hint_y=None,
                              height=dp(44)))
        self.scroll, self.box = make_scroll_column()
        root.add_widget(self.scroll)
        b = Btn(text="New Test", size_hint_y=None, height=dp(48))
        b.bind(on_release=lambda *_: app.new_test())
        root.add_widget(b)
        self.add_widget(root)


# ---------------------------------------------------------------- app
class MockTestApp(App):
    title = "Online Mock Test"

    def build(self):
        Window.clearcolor = BG
        self.questions = load_questions()
        self.sm = ScreenManager(transition=NoTransition())
        self.start_s = StartScreen(self)
        self.exam_s = ExamScreen(self)
        self.result_s = ResultScreen(self)
        self.review_s = ReviewScreen(self)
        for s in (self.start_s, self.exam_s, self.result_s, self.review_s):
            self.sm.add_widget(s)
        self.sm.current = "start"

        self.palette_view = None
        self.pal_btns = []
        self._tick_ev = None

        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_keyboard=self.on_back)
        return self.sm

    # ------------------------------------------------ state
    def start_test(self):
        n = len(self.questions)
        self.current = 0
        self.answers = [None] * n
        self.review = [False] * n
        self.visited = [False] * n
        self.end_ts = time.time() + TOTAL_SECONDS
        self.palette_view = None
        self.pal_btns = []
        self.sm.current = "exam"
        self.show_question()
        self.tick()
        if self._tick_ev:
            self._tick_ev.cancel()
        self._tick_ev = Clock.schedule_interval(self.tick, 1)

    def new_test(self):
        if self._tick_ev:
            self._tick_ev.cancel()
            self._tick_ev = None
        self.sm.current = "start"

    # ------------------------------------------------ timer
    def tick(self, *_):
        left = int(self.end_ts - time.time())
        if left <= 0:
            self.exam_s.timer_lbl.text = "Time Left: 0:00"
            self.submit_test()
            return False
        self.exam_s.timer_lbl.text = f"Time Left: {left // 60}:{left % 60:02d}"

    # ------------------------------------------------ question display
    def show_question(self):
        self.visited[self.current] = True
        q = self.questions[self.current]
        ex = self.exam_s
        ex.qno_lbl.text = f"Question: {self.current + 1} / {len(self.questions)}"
        ex.box.clear_widgets()
        ex.box.add_widget(WrapLabel(text=q["q"], font_size=sp(18)))
        for i, op in enumerate(q["options"]):
            ob = OptionButton(text=op, selected=(self.answers[self.current] == i))
            ob.bind(on_release=lambda _w, idx=i: self.select_option(idx))
            ex.box.add_widget(ob)
        ex.b_mark.text = ("Unmark Review" if self.review[self.current]
                          else "Mark Review")
        ex.scroll.scroll_y = 1
        self.update_palette()

    def select_option(self, idx):
        self.answers[self.current] = idx
        self.show_question()

    def clear_answer(self):
        self.answers[self.current] = None
        self.show_question()

    def toggle_review(self):
        self.review[self.current] = not self.review[self.current]
        self.show_question()

    def go_next(self):
        if self.current < len(self.questions) - 1:
            self.current += 1
            self.show_question()

    def go_prev(self):
        if self.current > 0:
            self.current -= 1
            self.show_question()

    def jump(self, i):
        self.current = i
        self.show_question()

    # ------------------------------------------------ palette
    def status_color(self, i):
        if self.review[i] and self.answers[i] is not None:
            return C_ANS_REVIEW
        if self.review[i]:
            return C_REVIEW
        if self.answers[i] is not None:
            return C_ANSWERED
        if self.visited[i]:
            return C_NOT_ANSWERED
        return C_NOT_VISITED

    def build_palette(self):
        view = ModalView(size_hint=(0.94, 0.85))
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        root.add_widget(Label(text="Question Palette", font_size=sp(18),
                              size_hint_y=None, height=dp(36)))
        sv = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=6, spacing=dp(6), size_hint_y=None,
                          row_default_height=dp(44), row_force_default=True)
        grid.bind(minimum_height=grid.setter("height"))
        self.pal_btns = []
        for i in range(len(self.questions)):
            b = Btn(text=str(i + 1), font_size=sp(13))
            b.bind(on_release=lambda _w, idx=i: (view.dismiss(), self.jump(idx)))
            self.pal_btns.append(b)
            grid.add_widget(b)
        sv.add_widget(grid)
        root.add_widget(sv)

        legend = GridLayout(cols=2, size_hint_y=None, height=dp(96),
                            spacing=dp(4))
        for text, col in (("Not Visited", C_NOT_VISITED),
                          ("Not Answered", C_NOT_ANSWERED),
                          ("Answered", C_ANSWERED),
                          ("Mark Review", C_REVIEW),
                          ("Answered & Review", C_ANS_REVIEW)):
            legend.add_widget(Btn(text=text, bg=col, font_size=sp(12),
                                  fg=(0, 0, 0, 1) if col == C_NOT_ANSWERED
                                  else (1, 1, 1, 1)))
        root.add_widget(legend)
        close = Btn(text="Close", size_hint_y=None, height=dp(44),
                    bg=(0.4, 0.4, 0.4, 1))
        close.bind(on_release=lambda *_: view.dismiss())
        root.add_widget(close)
        view.add_widget(root)
        self.palette_view = view

    def open_palette(self):
        if self.palette_view is None:
            self.build_palette()
        self.update_palette()
        self.palette_view.open()

    def update_palette(self):
        for i, b in enumerate(self.pal_btns):
            b.background_color = self.status_color(i)
            b.color = (0, 0, 0, 1) if self.status_color(i) == C_NOT_ANSWERED \
                else (1, 1, 1, 1)

    # ------------------------------------------------ submit / result
    def ask_submit(self):
        confirm_dialog("Are you sure you want to submit test?", self.submit_test)

    def submit_test(self):
        if self._tick_ev:
            self._tick_ev.cancel()
            self._tick_ev = None
        if self.palette_view:
            self.palette_view.dismiss()
        correct = wrong = unattempted = 0
        for i, q in enumerate(self.questions):
            if self.answers[i] is None:
                unattempted += 1
            elif self.answers[i] == q["answer"]:
                correct += 1
            else:
                wrong += 1
        score = correct - (wrong * NEGATIVE_VALUE if NEGATIVE_MARK else 0)
        total = len(self.questions)
        pct = score / total * 100
        self.result_s.result_lbl.text = (
            f"Correct Answer : {correct}\n"
            f"Wrong Answer : {wrong}\n"
            f"Unattempted : {unattempted}\n"
            f"Score : {score:.2f} / {total}\n"
            f"Percentage : {pct:.2f} %"
        )
        self.sm.current = "result"

    def show_review(self):
        box = self.review_s.box
        box.clear_widgets()
        for i, q in enumerate(self.questions):
            mine = ("Not Answered" if self.answers[i] is None
                    else q["options"][self.answers[i]])
            ok = self.answers[i] == q["answer"]
            colour = "008000" if ok else "cc0000"
            text = (f"[b]{escape_markup(q['q'])}[/b]\n\n"
                    f"Your Answer: [color={colour}]{escape_markup(mine)}[/color]\n"
                    f"Correct Answer: [color=008000]"
                    f"{escape_markup(q['options'][q['answer']])}[/color]")
            box.add_widget(WrapLabel(text=text, markup=True, font_size=sp(14)))
        self.review_s.scroll.scroll_y = 1
        self.sm.current = "review"

    # ------------------------------------------------ keyboard
    def on_key_down(self, _win, key, _scan, codepoint, _mod):
        if self.sm.current != "exam":
            return False
        ch = (codepoint or "").lower()
        if ch in ("a", "b", "c", "d"):
            idx = "abcd".index(ch)
            if idx < len(self.questions[self.current]["options"]):
                self.select_option(idx)
            return True
        if key == 276:        # left arrow
            self.go_prev()
            return True
        if key == 275:        # right arrow
            self.go_next()
            return True
        if key in (13, 271):  # Enter / keypad Enter
            self.go_next()
            return True
        return False

    def on_back(self, _win, key, *_):
        """Android back button (key 27): ask to submit instead of exiting."""
        if key == 27 and self.sm.current == "exam":
            self.ask_submit()
            return True
        return False


if __name__ == "__main__":
    MockTestApp().run()
