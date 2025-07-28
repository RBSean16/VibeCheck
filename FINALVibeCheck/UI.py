# UI.py

import flet as ft
import datetime
import requests
import threading
import calendar
from typing import Optional

# --- UI Constants ---
BG_COLOR = "#f8f9fa"
PRIMARY_COLOR = "#0d6efd"
WHITE = "#ffffff"
TEXT_COLOR = "#212529"
BLACK = "#000000"
TEXT_MUTED = "#6c757d"
BORDER_COLOR = "#dee2e6"
SUCCESS_COLOR = "#198754"
ERROR_COLOR = "#dc3545" 
SHADOW_COLOR = "#6c757d"

# --- API & App State ---
API_BASE_URL = "http://127.0.0.1:8000/api"
app_state = {"user_id": None, "user_name": None}

def main(page: ft.Page):
    page.title = "VibeCheck"
    page.bgcolor = BG_COLOR
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- UI Element Refs ---
    journal_entry_ref = ft.Ref[ft.TextField]()

    # --- MAIN UI VIEW CREATORS ---

    def create_login_view():
        login_username_field = ft.TextField(label="Username", autofocus=True, color=BLACK)
        login_password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, color=BLACK)
        error_text = ft.Text(value="", color=ERROR_COLOR, visible=False)

        def handle_login(e):
            error_text.visible = False
            page.update()
            if not login_username_field.value or not login_password_field.value:
                error_text.value = "Please enter a username and password."
                error_text.visible = True
                page.update()
                return
            try:
                response = requests.post(f"{API_BASE_URL}/login", json={"name": login_username_field.value, "password": login_password_field.value})
                if response.status_code == 200:
                    data = response.json()
                    app_state["user_id"] = data["user_id"]
                    app_state["user_name"] = data["name"]
                    page.go("/main")
                else:
                    error_text.value = response.json().get("detail", "An unknown error occurred.")
                    error_text.visible = True
                    page.update()
            except requests.exceptions.RequestException:
                error_text.value = "Cannot connect to the server."
                error_text.visible = True
                page.update()
        
        login_password_field.on_submit = handle_login

        return ft.View(
            "/",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Text("VibeCheck", size=32, weight=ft.FontWeight.BOLD, color=BLACK),
                        ft.Text("A Journal for Your Mind, A Map for Your Mood", color=TEXT_MUTED),
                        login_username_field,
                        login_password_field,
                        error_text,
                        ft.ElevatedButton("Login", width=400, on_click=handle_login, bgcolor=PRIMARY_COLOR, color=WHITE),
                        ft.Column(
                            [
                                ft.Text("No account yet?"),
                                ft.TextButton("Create one here.", on_click=lambda _: page.go("/register"), style=ft.ButtonStyle(padding=0)),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                        ),
                    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=400, padding=40, border_radius=10, bgcolor=WHITE,
                    shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.1, SHADOW_COLOR)),
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def create_registration_view():
        reg_username_field = ft.TextField(label="Username", autofocus=True, color=BLACK)
        reg_password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, color=BLACK)
        error_text = ft.Text(value="", color=ERROR_COLOR, visible=False)

        def handle_registration(e):
            error_text.visible = False
            page.update()
            if not reg_username_field.value or not reg_password_field.value:
                error_text.value = "Username and password cannot be empty."
                error_text.visible = True
                page.update()
                return
            try:
                response = requests.post(f"{API_BASE_URL}/register", json={"name": reg_username_field.value, "password": reg_password_field.value})
                if response.status_code == 200:
                    page.snack_bar = ft.SnackBar(content=ft.Text("Account created! Please log in."), bgcolor=SUCCESS_COLOR)
                    page.snack_bar.open = True
                    page.go("/")
                else:
                    error_text.value = response.json().get("detail", "Registration failed.")
                    error_text.visible = True
                    page.update()
            except requests.exceptions.RequestException:
                error_text.value = "Cannot connect to the server."
                error_text.visible = True
                page.update()
        
        reg_password_field.on_submit = handle_registration

        return ft.View(
            "/register",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Text("Create Your Account", size=24, weight=ft.FontWeight.BOLD, color=BLACK),
                        reg_username_field,
                        reg_password_field,
                        error_text,
                        ft.ElevatedButton("Create Account", width=400, on_click=handle_registration, bgcolor=SUCCESS_COLOR, color=WHITE),
                    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=400, padding=40, border_radius=10, bgcolor=WHITE,
                    shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.1, SHADOW_COLOR)),
                )
            ],
            appbar=ft.AppBar(title=ft.Text("Register"), leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"))),
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def create_mood_tracker_view():
        content_area = ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        def build_today_view():
            mood_map = {9: "😄", 7: "😊", 5: "😐", 3: "😟", 1: "😠"}
            score_to_label_map = {9: "Happy", 7: "Content", 5: "Neutral", 3: "Sad", 1: "Angry"}
            color_map = {9: ft.Colors.GREEN_200, 7: ft.Colors.LIGHT_GREEN_300, 5: ft.Colors.YELLOW_200, 3: ft.Colors.AMBER_300, 1: ft.Colors.RED_200}
            
            timeline = ft.ListView(expand=True, spacing=10, auto_scroll=True)
            timeline.controls.append(ft.Text(datetime.date.today().strftime("%A, %B %d"), size=20, weight=ft.FontWeight.BOLD, color=BLACK))
            
            try:
                response = requests.get(f"{API_BASE_URL}/today-moods/{app_state['user_id']}")
                if response.status_code == 200:
                    moods = response.json()
                    if not moods:
                        timeline.controls.append(ft.Text("No moods logged yet today.", color=TEXT_MUTED, italic=True))
                    for mood in moods:
                        mood_date = datetime.datetime.fromisoformat(mood['date'])
                        mood_score = mood['mood_score']
                        mood_label = score_to_label_map.get(mood_score, "a certain way")

                        mood_card = ft.Container(
                            content=ft.Row([
                                ft.Text(mood_map.get(mood_score, "❓"), size=24),
                                ft.Text(f"You felt {mood_label}", expand=True, color=BLACK),
                                ft.Text(mood_date.strftime("%I:%M %p"), color=BLACK),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            width=400,
                            padding=15,
                            border_radius=8,
                            bgcolor=color_map.get(mood_score, ft.Colors.GREY_300)
                        )
                        timeline.controls.append(mood_card)
            except requests.exceptions.RequestException: pass
            
            return ft.Container(content=timeline, expand=True, alignment=ft.alignment.center)

        def build_line_chart_view(timespan: str):
            url = f"{API_BASE_URL}/mood-chart/{app_state['user_id']}?timespan={timespan}&v={datetime.datetime.now().timestamp()}"
            return ft.Container(
                content=ft.Image(
                    src=url,
                    fit=ft.ImageFit.CONTAIN,
                ),
                expand=True,
            )

        def update_view(e, timespan: str):
            content_area.controls.clear()
            content_area.controls.append(ft.ProgressRing())
            page.update()

            if timespan == "today":
                content_area.controls.clear()
                content_area.controls.append(build_today_view())
                page.update()
                return

            try:
                check_url = f"{API_BASE_URL}/mood-data-check/{app_state['user_id']}?timespan={timespan}"
                response = requests.get(check_url)
                content_area.controls.clear()

                if response.status_code == 200 and response.json().get("has_enough_data"):
                    content_area.controls.append(build_line_chart_view(timespan))
                else:
                    message = f"Not enough mood data for the last {timespan.replace('d', '')} days. Keep logging to see your trend!"
                    content_area.controls.append(
                        ft.Column([
                            ft.Icon(name=ft.Icons.INFO_OUTLINE, size=48, color=TEXT_MUTED),
                            ft.Text(
                                value=message,
                                size=16,
                                color=TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                                italic=True,
                                width=400
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10)
                    )
            except requests.exceptions.RequestException:
                content_area.controls.clear()
                content_area.controls.append(ft.Text("Error: Could not connect to the server.", color=ERROR_COLOR))

            page.update()
        
        update_view(None, "today")

        return ft.View(
            "/mood-tracker",
            controls=[
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.ElevatedButton("Today", on_click=lambda e: update_view(e, "today")),
                                ft.ElevatedButton("Last 7 Days", on_click=lambda e: update_view(e, "7d")),
                                ft.ElevatedButton("Last 30 Days", on_click=lambda e: update_view(e, "30d")),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        content_area
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            appbar=ft.AppBar(
                title=ft.Text("Your Mood Trends"),
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/main"))
            ),
            bgcolor=BG_COLOR,
            padding=20
        )

    def create_journal_history_view():
        entries_list = ft.ListView(expand=True, spacing=10, padding=20)

        def handle_delete(e):
            entry_id = e.control.data
            try:
                response = requests.delete(f"{API_BASE_URL}/journal/{entry_id}")
                if response.status_code == 200:
                    entry_container_to_remove = e.control.parent.parent
                    entries_list.controls.remove(entry_container_to_remove)
                    page.update()
            except requests.exceptions.RequestException: pass

        try:
            response = requests.get(f"{API_BASE_URL}/journals/{app_state['user_id']}")
            if response.status_code == 200:
                entries = response.json()
                if not entries:
                    entries_list.controls.append(ft.Text("You have no journal entries yet.", italic=True, color=TEXT_MUTED))
                for entry in entries:
                    entries_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(entry['date'], weight=ft.FontWeight.BOLD),
                                    ft.Text(entry['content'], selectable=True),
                                ], expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                                    data=entry['id'], on_click=handle_delete, tooltip="Delete Entry"
                                ),
                            ]),
                            padding=15, border=ft.border.all(1, BORDER_COLOR), border_radius=10
                        )
                    )
        except requests.exceptions.RequestException:
            entries_list.controls.append(ft.Text("Could not load entries. Connection error.", color=ERROR_COLOR))

        return ft.View(
            "/journal-history",
            [entries_list],
            appbar=ft.AppBar(
                title=ft.Text("Your Past Entries"),
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/main"))
            )
        )

    def create_main_view():
        recommendation_text = ft.Ref[ft.Text]()
        mood_confirmation_text = ft.Ref[ft.Text]()
        journal_confirmation_text = ft.Ref[ft.Text]()
        
        calendar_header = ft.Text(size=16, weight=ft.FontWeight.BOLD, expand=True, text_align=ft.TextAlign.CENTER, color=BLACK)
        calendar_grid = ft.GridView(expand=False, runs_count=7, max_extent=50, child_aspect_ratio=1.0, spacing=5, run_spacing=5)
        
        wellness_quote_text = ft.Text(value="Loading tip...", italic=True, color=BLACK)
        wellness_author_text = ft.Text(text_align=ft.TextAlign.RIGHT, color=BLACK)

        current_date = datetime.date.today()

        def show_confirmation(conf_text_ref: ft.Ref[ft.Text], message: str, color: str):
            def hide_confirmation():
                if conf_text_ref.current:
                    conf_text_ref.current.visible = False
                    page.update()
            
            if conf_text_ref.current:
                conf_text_ref.current.value = message
                conf_text_ref.current.color = color
                conf_text_ref.current.visible = True
                page.update()
                threading.Timer(3.0, hide_confirmation).start()

        def update_calendar(date_to_display: datetime.date):
            nonlocal current_date
            current_date = date_to_display
            
            if not calendar_header or not calendar_grid: return

            calendar_header.value = current_date.strftime("%B %Y")
            calendar_grid.controls.clear()

            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                calendar_grid.controls.append(ft.Container(ft.Text(day, weight=ft.FontWeight.BOLD, color=TEXT_MUTED), alignment=ft.alignment.center))

            first_day_of_month, days_in_month = calendar.monthrange(current_date.year, current_date.month)
            
            prev_month_date = current_date - datetime.timedelta(days=1)
            _, days_in_prev_month = calendar.monthrange(prev_month_date.year, prev_month_date.month)
            for i in range(first_day_of_month):
                day_num = days_in_prev_month - first_day_of_month + i + 1
                calendar_grid.controls.append(
                    ft.Container(content=ft.Text(str(day_num)), alignment=ft.alignment.center, opacity=0.35)
                )

            entry_dates = set()
            try:
                response = requests.get(f"{API_BASE_URL}/activity-dates/{app_state['user_id']}")
                if response.status_code == 200:
                    entry_dates = set(response.json().get("dates", []))
            except requests.exceptions.RequestException: pass

            today_str = datetime.date.today().isoformat()
            for day_num in range(1, days_in_month + 1):
                day_date = datetime.date(current_date.year, current_date.month, day_num)
                day_str = day_date.isoformat()
                is_today = (day_str == today_str)
                has_entry = day_str in entry_dates

                day_container = ft.Container(
                    content=ft.Text(str(day_num)), alignment=ft.alignment.center,
                    border_radius=20, data=day_str
                )

                if is_today:
                    day_container.bgcolor = PRIMARY_COLOR
                    day_container.content.color = WHITE
                elif has_entry:
                    day_container.bgcolor = ft.Colors.with_opacity(0.3, SUCCESS_COLOR)
                    day_container.content.color = BLACK
                else:
                    day_container.content.color = TEXT_COLOR
                
                calendar_grid.controls.append(day_container)
            
            total_cells = first_day_of_month + days_in_month
            target_cells = 42 if total_cells > 35 else 35
            remaining_cells = target_cells - total_cells

            for i in range(remaining_cells):
                calendar_grid.controls.append(
                    ft.Container(content=ft.Text(str(i + 1)), alignment=ft.alignment.center, opacity=0.35)
                )
            page.update()

        def change_month(e, delta: int):
            nonlocal current_date
            new_month = current_date.month + delta
            new_year = current_date.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            elif new_month < 1:
                new_month = 12
                new_year -= 1
            update_calendar(datetime.date(new_year, new_month, 1))

        def select_mood(e):
            if not app_state["user_id"]: return
            score_map = {"Happy": 9, "Content": 7, "Neutral": 5, "Sad": 3, "Angry": 1}
            label = e.control.data
            score = score_map.get(label, 5)
            try:
                requests.post(f"{API_BASE_URL}/mood-entry", json={"user_id": app_state["user_id"], "mood_score": score, "notes": f"Selected mood: {label}"})
                show_confirmation(mood_confirmation_text, f"Mood '{label}' saved!", SUCCESS_COLOR)
                for item_container in e.control.parent.controls:
                    is_selected = (item_container == e.control)
                    item_container.bgcolor = PRIMARY_COLOR if is_selected else WHITE
                    item_container.border = ft.border.all(2, PRIMARY_COLOR if is_selected else BORDER_COLOR)
                    item_container.content.controls[0].color = WHITE if is_selected else TEXT_COLOR
                    item_container.content.controls[1].color = WHITE if is_selected else TEXT_MUTED
                update_calendar(current_date)
                page.update()
            except requests.exceptions.RequestException: 
                show_confirmation(mood_confirmation_text, "Connection error.", ERROR_COLOR)

        def save_entry(e):
            if not app_state["user_id"]: return
            content = journal_entry_ref.current.value
            if not content:
                show_confirmation(journal_confirmation_text, "Journal entry is empty.", ERROR_COLOR)
                return
            try:
                requests.post(f"{API_BASE_URL}/journal-entry", json={"user_id": app_state["user_id"], "content": content})
                journal_entry_ref.current.value = ""
                show_confirmation(journal_confirmation_text, "Journal entry saved!", SUCCESS_COLOR)
                update_calendar(current_date)
                page.update()
            except requests.exceptions.RequestException: 
                show_confirmation(journal_confirmation_text, "Connection error.", ERROR_COLOR)

        def get_ai_recommendation(e):
            try:
                response = requests.get(f"{API_BASE_URL}/recommendation/{app_state['user_id']}")
                if response.status_code == 200:
                    suggestion = response.json().get("recommendation", "Could not get a recommendation.")
                    recommendation_text.current.value = suggestion
                    recommendation_text.current.visible = True
                    page.update()
                else:
                    show_confirmation(mood_confirmation_text, "Could not fetch insights.", ERROR_COLOR)
            except requests.exceptions.RequestException:
                show_confirmation(mood_confirmation_text, "Connection error.", ERROR_COLOR)
        
        def fetch_wellness_tip():
            try:
                response = requests.get(f"{API_BASE_URL}/wellness-tip")
                if response.status_code == 200:
                    data = response.json()
                    wellness_quote_text.value = f"\"{data.get('quote')}\""
                    wellness_author_text.value = f"- {data.get('author')}"
                    page.update()
            except requests.exceptions.RequestException: pass

        mood_items = []
        moods = [("😄", "Happy"), ("😊", "Content"), ("😐", "Neutral"), ("😟", "Sad"), ("😠", "Angry")]
        for icon, label in moods:
            mood_items.append(
                ft.Container(
                    content=ft.Column([ft.Text(icon, size=30), ft.Text(label, size=12, color=TEXT_MUTED)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    on_click=select_mood, data=label, padding=10, border_radius=8, border=ft.border.all(1, BORDER_COLOR), tooltip=f"Select {label}"
                )
            )
        
        left_sidebar = ft.Container(
            content=ft.Column([
                ft.Text("How are you feeling?", weight=ft.FontWeight.BOLD, size=20, color=BLACK),
                ft.Row(controls=mood_items, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                ft.Text(ref=mood_confirmation_text, visible=False, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Divider(),
                ft.Text("Journaling Activity", weight=ft.FontWeight.BOLD, size=18, color=BLACK),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=lambda e: change_month(e, -1)),
                    calendar_header,
                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda e: change_month(e, 1)),
                ]),
                calendar_grid
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            width=400, padding=20, bgcolor=WHITE, border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, SHADOW_COLOR))
        )
        main_content = ft.Container(
            content=ft.Column([
                ft.Text(f"Journal Entry for {datetime.date.today().strftime('%B %d, %Y')}", weight=ft.FontWeight.BOLD, size=18, color=BLACK),
                ft.TextField(ref=journal_entry_ref, multiline=True, min_lines=10, expand=True, border_color=BORDER_COLOR, color=BLACK),
                ft.Text(ref=journal_confirmation_text, visible=False, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Row([
                    ft.ElevatedButton("Save Entry", on_click=save_entry, icon=ft.Icons.SAVE, bgcolor=PRIMARY_COLOR, color=WHITE),
                    ft.ElevatedButton("View Past Entries", on_click=lambda _: page.go("/journal-history"), icon=ft.Icons.HISTORY)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=15, expand=True),
            expand=True, padding=20, bgcolor=WHITE, border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, SHADOW_COLOR))
        )
        right_sidebar = ft.Container(
            content=ft.Column([
                ft.Text("Insights & Visuals", weight=ft.FontWeight.BOLD, size=18, color=BLACK),
                ft.ElevatedButton("Get AI Insight", icon=ft.Icons.INSIGHTS, on_click=get_ai_recommendation),
                ft.Text(ref=recommendation_text, value="", visible=False, italic=True, color=BLACK),
                ft.Divider(),
                ft.ElevatedButton("View Mood Trends", icon=ft.Icons.CALENDAR_VIEW_WEEK, on_click=lambda _: page.go("/mood-tracker")),
                ft.Divider(),
                ft.Text("Daily Wellness Tip", weight=ft.FontWeight.BOLD, size=16, color=BLACK),
                wellness_quote_text,
                wellness_author_text,
                ft.Divider(),
                ft.Text("Support Resources (PH)", weight=ft.FontWeight.BOLD, size=16, color=BLACK),
                ft.TextButton("WHO Philippines", url="https://www.who.int/philippines", style=ft.ButtonStyle(padding=0)),
                ft.Text("Official information on health in the Philippines.", size=10, color=TEXT_MUTED),
                ft.TextButton("NCMH Crisis Hotline (Facebook)", url="https://www.facebook.com/ncmhcrisishotline/", style=ft.ButtonStyle(padding=0)),
                ft.Text("24/7 crisis support from the National Center for Mental Health.", size=10, color=TEXT_MUTED),
                ft.TextButton("MindNation", url="https://www.mindnation.com/", style=ft.ButtonStyle(padding=0)),
                ft.Text("Online platform for booking therapy and counseling sessions.", size=10, color=TEXT_MUTED),
                ft.TextButton("Philippine Mental Health Association", url="https://pmha.org.ph/", style=ft.ButtonStyle(padding=0)),
                ft.Text("A national organization for mental health advocacy and services.", size=10, color=TEXT_MUTED),
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            width=300, padding=20, bgcolor=WHITE, border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, SHADOW_COLOR))
        )
        
        update_calendar(current_date)
        fetch_wellness_tip()

        return ft.View(
            "/main",
            [
                ft.Row(
                    [left_sidebar, main_content, right_sidebar], 
                    spacing=20, 
                    expand=True
                )
            ],
            appbar=ft.AppBar(
                title=ft.Text(f"VibeCheck - {app_state.get('user_name', '')}"),
                actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Logout", on_click=lambda _: page.go("/"))],
            ),
        )

    # --- Route Management ---
    def route_change(e):
        page.views.clear()
        if page.route == "/main":
            page.views.append(create_main_view())
        elif page.route == "/register":
            page.views.append(create_registration_view())
        elif page.route == "/mood-tracker":
            page.views.append(create_mood_tracker_view())
        elif page.route == "/journal-history": 
            page.views.append(create_journal_history_view())
        else:
            app_state["user_id"] = None
            app_state["user_name"] = None
            page.views.append(create_login_view())
        page.update()

    page.on_route_change = route_change
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)