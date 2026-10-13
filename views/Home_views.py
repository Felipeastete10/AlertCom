from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.card import MDCard

Builder.load_file('views/home.kv')

class HomeScreen(MDScreen):
    def ir_a_reporte(self):
        # Llama a la navegación global de Felipe Astete
        app = self.manager.parent  # o self.manager según cómo lo armó Felipe
        if hasattr(app, 'go_to_screen'):
            app.go_to_screen('report')
        else:
            # Alternativa si Felipe usó ScreenManager directo
            self.manager.current = 'report'