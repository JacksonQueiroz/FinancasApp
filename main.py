from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, RoundedRectangle
from datetime import datetime, timedelta
import sqlite3
import os
import calendar

Window.clearcolor = (0.12, 0.12, 0.12, 1) # Cor de fundo mais suave

if platform == 'android':
    from android.storage import app_storage_path
    DB_PATH = os.path.join(app_storage_path(), "financas_android.db")
else:
    DB_PATH = "financas_android.db"

def conectar():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = conectar()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipo TEXT NOT NULL, usuario TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT NOT NULL, valor REAL NOT NULL, tipo TEXT NOT NULL, categoria TEXT, data TEXT NOT NULL, data_vencimento TEXT, pago INTEGER DEFAULT 0, usuario TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT NOT NULL, valor_alvo REAL NOT NULL, valor_atual REAL DEFAULT 0, usuario TEXT NOT NULL)")
    
    for usr in ['Jackson', 'Elcione']:
        cur.execute("SELECT COUNT(*) FROM categorias WHERE usuario=?", (usr,))
        if cur.fetchone()[0] == 0:
            padrao = [("Salário","renda"),("Freelance","renda"),("Alimentação","despesa"),("Moradia","despesa"),("Transporte","despesa"),("Lazer","despesa"),("Saúde","despesa"),("Outros","despesa")]
            for nome, tipo in padrao:
                cur.execute("INSERT INTO categorias (nome, tipo, usuario) VALUES (?,?,?)", (nome, tipo, usr))
    con.commit()
    con.close()

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============ COMPONENTES VISUAIS ============

class CardDashboard(BoxLayout):
    def __init__(self, titulo, valor, cor_fundo, cor_texto, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(110), padding=dp(15), spacing=dp(5), **kwargs)
        
        # Desenha o fundo do cartão com bordas arredondadas
        with self.canvas.before:
            Color(*cor_fundo)
            self.rect = RoundedRectangle(radius=[dp(10)], pos=self.pos, size=self.size)
        self.bind(pos=self.atualizar_rect, size=self.atualizar_rect)

        lbl_titulo = Label(text=titulo, font_size='14sp', color=(0.8, 0.8, 0.8, 1), size_hint_y=0.4, halign="left", valign="bottom")
        lbl_titulo.bind(size=lbl_titulo.setter('text_size'))
        
        lbl_valor = Label(text=valor, font_size='24sp', bold=True, color=cor_texto, size_hint_y=0.6, halign="left", valign="top")
        lbl_valor.bind(size=lbl_valor.setter('text_size'))

        self.add_widget(lbl_titulo)
        self.add_widget(lbl_valor)

    def atualizar_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class CalendarioPopup(ModalView):
    def __init__(self, botao_pai, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.7)
        self.background_color = (0, 0, 0, 0.8)
        self.botao_pai = botao_pai
        self.ano_atual = datetime.now().year
        self.mes_atual = datetime.now().month
        self.layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        self.add_widget(self.layout)
        self.desenhar_calendario()

    def desenhar_calendario(self):
        self.layout.clear_widgets()
        
        topo = BoxLayout(size_hint_y=None, height=dp(50))
        btn_ant = Button(text="<", size_hint_x=0.2, background_color=(0.3, 0.3, 0.3, 1), on_release=self.mes_anterior)
        lbl_mes = Label(text=f"{calendar.month_name[self.mes_atual].capitalize()} {self.ano_atual}", bold=True, font_size='20sp')
        btn_prox = Button(text=">", size_hint_x=0.2, background_color=(0.3, 0.3, 0.3, 1), on_release=self.proximo_mes)
        topo.add_widget(btn_ant); topo.add_widget(lbl_mes); topo.add_widget(btn_prox)
        self.layout.add_widget(topo)

        dias_semana = ["D", "S", "T", "Q", "Q", "S", "S"]
        grid_semana = GridLayout(cols=7, size_hint_y=None, height=dp(30))
        for d in dias_semana:
            grid_semana.add_widget(Label(text=d, bold=True, color=(0.7,0.7,0.7,1)))
        self.layout.add_widget(grid_semana)

        grid_dias = GridLayout(cols=7)
        cal = calendar.monthcalendar(self.ano_atual, self.mes_atual)
        
        for semana in cal:
            for dia in semana:
                if dia == 0:
                    grid_dias.add_widget(Label(text=""))
                else:
                    btn = Button(text=str(dia), background_color=(0.2, 0.5, 0.8, 1))
                    btn.bind(on_release=lambda x, d=dia: self.selecionar_dia(d))
                    grid_dias.add_widget(btn)
        self.layout.add_widget(grid_dias)

        self.layout.add_widget(Button(text="Cancelar", size_hint_y=None, height=dp(45), background_color=(0.8, 0.3, 0.3, 1), on_release=self.dismiss))

    def mes_anterior(self, instance):
        self.mes_atual -= 1
        if self.mes_atual < 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        self.desenhar_calendario()

    def proximo_mes(self, instance):
        self.mes_atual += 1
        if self.mes_atual > 12:
            self.mes_atual = 1
            self.ano_atual += 1
        self.desenhar_calendario()

    def selecionar_dia(self, dia):
        self.botao_pai.text = f"{dia:02d}/{self.mes_atual:02d}/{self.ano_atual}"
        self.dismiss()

class BotaoData(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = datetime.now().strftime("%d/%m/%Y")
        self.background_color = (0.2, 0.5, 0.8, 1)
        self.bind(on_release=self.abrir_calendario)

    def abrir_calendario(self, instance):
        CalendarioPopup(self).open()

# ============ TELAS ============

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        layout.add_widget(Label(text="Finanças Mobile", font_size='32sp', bold=True, size_hint_y=0.3))
        layout.add_widget(Label(text="Quem está acessando?", font_size='18sp', size_hint_y=0.1))

        btn_jackson = Button(text="Jackson", font_size='20sp', background_color=(0.2, 0.6, 0.8, 1), size_hint_y=None, height=dp(60))
        btn_jackson.bind(on_press=lambda x: self.login("Jackson"))
        layout.add_widget(btn_jackson)

        btn_elcione = Button(text="Elcione", font_size='20sp', background_color=(0.8, 0.4, 0.6, 1), size_hint_y=None, height=dp(60))
        btn_elcione.bind(on_press=lambda x: self.login("Elcione"))
        layout.add_widget(btn_elcione)
        self.add_widget(layout)

    def login(self, usuario):
        App.get_running_app().usuario_atual = usuario
        self.manager.current = 'main'
        self.manager.get_screen('main').atualizar_tudo()

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.content_area = BoxLayout(orientation='vertical', padding=dp(10))
        self.layout.add_widget(self.content_area)

        # Menu Inferior
        nav = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(2))
        
        btn_dash = Button(text="Início", background_color=(0.25, 0.25, 0.25, 1))
        btn_dash.bind(on_press=self.show_dashboard)
        
        btn_trans = Button(text="Contas", background_color=(0.25, 0.25, 0.25, 1))
        btn_trans.bind(on_press=self.show_transacoes)
        
        btn_add = Button(text="+ Novo", background_color=(0.1, 0.7, 0.4, 1), bold=True)
        btn_add.bind(on_press=self.popup_nova_transacao)
        
        btn_metas = Button(text="Metas", background_color=(0.25, 0.25, 0.25, 1))
        btn_metas.bind(on_press=self.show_metas)

        nav.add_widget(btn_dash)
        nav.add_widget(btn_trans)
        nav.add_widget(btn_add)
        nav.add_widget(btn_metas)
        self.layout.add_widget(nav)
        self.add_widget(self.layout)

    def atualizar_tudo(self):
        self.show_dashboard()

    def show_dashboard(self, instance=None):
        self.content_area.clear_widgets()
        user = App.get_running_app().usuario_atual
        
        con = conectar(); cur = con.cursor()
        mes_atual = datetime.now().strftime("%Y-%m")
        
        query_renda = """SELECT COALESCE(SUM(valor),0) FROM transacoes 
                         WHERE tipo='renda' AND usuario=? 
                         AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ?"""
        cur.execute(query_renda, (user, f"{mes_atual}%"))
        renda = cur.fetchone()[0]
        
        query_despesa = """SELECT COALESCE(SUM(valor),0) FROM transacoes 
                           WHERE tipo='despesa' AND usuario=? 
                           AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ?"""
        cur.execute(query_despesa, (user, f"{mes_atual}%"))
        despesa = cur.fetchone()[0]
        
        hoje = datetime.now().date()
        daqui_3 = (hoje + timedelta(days=3)).strftime("%Y-%m-%d")
        cur.execute("SELECT COUNT(*) FROM transacoes WHERE usuario=? AND pago=0 AND tipo='despesa' AND data_vencimento >= ? AND data_vencimento <= ?", 
                    (user, hoje.strftime("%Y-%m-%d"), daqui_3))
        vencendo = cur.fetchone()[0]
        con.close()

        saldo = renda - despesa

        # Rolagem para a tela não quebrar
        scroll = ScrollView()
        dash = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, padding=dp(5))
        dash.bind(minimum_height=dash.setter('height'))
        
        # Cabeçalho
        header = Label(text=f"Olá, {user}!", font_size='24sp', bold=True, size_hint_y=None, height=dp(50), halign="left", valign="middle")
        header.bind(size=header.setter('text_size'))
        dash.add_widget(header)

        # Aviso de Vencimento
        if vencendo > 0:
            btn_aviso = Button(text=f"Atenção: {vencendo} conta(s) vencendo em breve!", 
                               background_color=(0.9, 0.3, 0.3, 1), 
                               size_hint_y=None, height=dp(45), bold=True)
            btn_aviso.bind(on_press=self.show_transacoes)
            dash.add_widget(btn_aviso)

        # Cards com cores de fundo mais suaves
        dash.add_widget(CardDashboard("Renda do Mês", formatar_moeda(renda), (0.1, 0.4, 0.2, 1), (0.3, 1, 0.5, 1)))
        dash.add_widget(CardDashboard("Despesas do Mês", formatar_moeda(despesa), (0.4, 0.1, 0.1, 1), (1, 0.4, 0.4, 1)))
        dash.add_widget(CardDashboard("Saldo do Mês", formatar_moeda(saldo), (0.1, 0.2, 0.4, 1), (0.4, 0.7, 1, 1)))
        
        scroll.add_widget(dash)
        self.content_area.add_widget(scroll)

    def show_transacoes(self, instance=None):
        self.content_area.clear_widgets()
        user = App.get_running_app().usuario_atual
        
        con = conectar(); cur = con.cursor()
        mes_atual = datetime.now().strftime("%Y-%m")
        
        query = """SELECT id, descricao, valor, tipo, data, data_vencimento, pago 
                   FROM transacoes WHERE usuario=? 
                   AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ? 
                   ORDER BY pago ASC, data DESC"""
        cur.execute(query, (user, f"{mes_atual}%"))
        rows = cur.fetchall()
        con.close()

        scroll = ScrollView()
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=dp(5))
        lista.bind(minimum_height=lista.setter('height'))

        if not rows:
            lista.add_widget(Label(text="Nenhuma conta para este mês.", size_hint_y=None, height=dp(50), color=(0.7,0.7,0.7,1)))

        for tid, desc, valor, tipo, data, venc, pago in rows:
            card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), spacing=dp(10), padding=dp(10))
            
            # Fundo do cartão da lista
            with card.canvas.before:
                Color(0.2, 0.2, 0.2, 1) if not pago else Color(0.15, 0.15, 0.15, 1)
                card_rect = RoundedRectangle(radius=[dp(8)], pos=card.pos, size=card.size)
            card.bind(pos=lambda obj, val, r=card_rect: setattr(r, 'pos', val), 
                      size=lambda obj, val, r=card_rect: setattr(r, 'size', val))

            cor_txt = (0.3, 1, 0.5, 1) if tipo == 'renda' else (1, 0.4, 0.4, 1)
            if pago: cor_txt = (0.5, 0.5, 0.5, 1)

            info = BoxLayout(orientation='vertical')
            lbl_d = Label(text=desc, halign="left", valign="middle", color=cor_txt, bold=True, font_size='16sp')
            lbl_d.bind(size=lbl_d.setter('text_size'))
            
            texto_data = f"Venc: {venc[8:10]}/{venc[5:7]}" if venc else f"Data: {data[8:10]}/{data[5:7]}"
            if pago: texto_data += " (PAGO)"
            lbl_data = Label(text=texto_data, halign="left", valign="middle", font_size='12sp', color=(0.6,0.6,0.6,1))
            lbl_data.bind(size=lbl_data.setter('text_size'))
            
            info.add_widget(lbl_d)
            info.add_widget(lbl_data)

            lbl_val = Label(text=formatar_moeda(valor), color=cor_txt, bold=True, size_hint_x=0.4, halign="right", valign="middle", font_size='16sp')
            lbl_val.bind(size=lbl_val.setter('text_size'))

            card.add_widget(info)
            card.add_widget(lbl_val)

            if not pago and tipo == 'despesa':
                btn_pagar = Button(text="Pagar", size_hint_x=None, width=dp(70), background_color=(0.1, 0.6, 0.3, 1), bold=True)
                btn_pagar.bind(on_press=lambda x, i=tid: self.marcar_pago(i))
                card.add_widget(btn_pagar)

            lista.add_widget(card)

        scroll.add_widget(lista)
        self.content_area.add_widget(scroll)

    def marcar_pago(self, tid):
        con = conectar()
        con.execute("UPDATE transacoes SET pago=1 WHERE id=?", (tid,))
        con.commit(); con.close()
        self.show_transacoes()

    def show_metas(self, instance=None):
        self.content_area.clear_widgets()
        user = App.get_running_app().usuario_atual
        con = conectar(); cur = con.cursor()
        cur.execute("SELECT id, descricao, valor_alvo, valor_atual FROM metas WHERE usuario=?", (user,))
        metas = cur.fetchall(); con.close()

        scroll = ScrollView()
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        lista.bind(minimum_height=lista.setter('height'))

        btn_nova = Button(text="Cadastrar Nova Meta", size_hint_y=None, height=dp(50), background_color=(0.2, 0.5, 0.8, 1), bold=True)
        btn_nova.bind(on_press=self.popup_nova_meta)
        lista.add_widget(btn_nova)

        for mid, desc, alvo, atual in metas:
            prog = min(atual / alvo, 1.0) if alvo > 0 else 0
            
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10), spacing=dp(5))
            with card.canvas.before:
                Color(0.2, 0.2, 0.2, 1)
                card_rect = RoundedRectangle(radius=[dp(8)], pos=card.pos, size=card.size)
            card.bind(pos=lambda obj, val, r=card_rect: setattr(r, 'pos', val), 
                      size=lambda obj, val, r=card_rect: setattr(r, 'size', val))

            card.add_widget(Label(text=desc, bold=True, font_size='18sp', size_hint_y=0.4))
            card.add_widget(Label(text=f"{formatar_moeda(atual)} de {formatar_moeda(alvo)} ({prog*100:.0f}%)", size_hint_y=0.3))
            
            btn_guardar = Button(text="Guardar Dinheiro", background_color=(0.1, 0.6, 0.3, 1), size_hint_y=0.4)
            btn_guardar.bind(on_press=lambda x, i=mid, a=atual: self.popup_guardar_meta(i, a))
            card.add_widget(btn_guardar)
            
            lista.add_widget(card)
        scroll.add_widget(lista)
        self.content_area.add_widget(scroll)

    def popup_guardar_meta(self, mid, atual):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        ent = TextInput(hint_text="Valor (R$)", input_filter='float', multiline=False, size_hint_y=None, height=dp(40))
        btn = Button(text="Salvar", size_hint_y=None, height=dp(45), background_color=(0.1, 0.6, 0.3, 1))
        content.add_widget(ent); content.add_widget(btn)
        popup = Popup(title="Guardar Dinheiro", content=content, size_hint=(0.8, 0.4))

        def salvar(instance):
            try:
                val = float(ent.text.replace(",", "."))
                con = conectar(); con.execute("UPDATE metas SET valor_atual=? WHERE id=?", (atual + val, mid))
                con.commit(); con.close(); popup.dismiss(); self.show_metas()
            except: pass
        btn.bind(on_press=salvar); popup.open()

    def popup_nova_meta(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        ent_desc = TextInput(hint_text="Ex: Viagem", multiline=False, size_hint_y=None, height=dp(40))
        ent_val = TextInput(hint_text="Valor Alvo (R$)", input_filter='float', multiline=False, size_hint_y=None, height=dp(40))
        btn = Button(text="Criar Meta", size_hint_y=None, height=dp(45), background_color=(0.1, 0.6, 0.3, 1))
        content.add_widget(ent_desc); content.add_widget(ent_val); content.add_widget(btn)
        popup = Popup(title="Nova Meta", content=content, size_hint=(0.9, 0.5))

        def salvar(instance):
            try:
                val = float(ent_val.text.replace(",", "."))
                con = conectar(); con.execute("INSERT INTO metas (descricao, valor_alvo, usuario) VALUES (?,?,?)", 
                            (ent_desc.text, val, App.get_running_app().usuario_atual))
                con.commit(); con.close(); popup.dismiss(); self.show_metas()
            except: pass
        btn.bind(on_press=salvar); popup.open()

    def popup_nova_transacao(self, instance):
        user = App.get_running_app().usuario_atual
        con = conectar(); cur = con.cursor()
        cur.execute("SELECT nome FROM categorias WHERE tipo='despesa' AND usuario=?", (user,))
        cats_desp = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT nome FROM categorias WHERE tipo='renda' AND usuario=?", (user,))
        cats_ren = [r[0] for r in cur.fetchall()]
        con.close()

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        spin_tipo = Spinner(text='Despesa', values=('Despesa', 'Renda'), size_hint_y=None, height=dp(45), background_color=(0.3, 0.3, 0.3, 1))
        ent_desc = TextInput(hint_text="Descrição (Ex: Mercado)", multiline=False, size_hint_y=None, height=dp(40))
        ent_val = TextInput(hint_text="Valor (Ex: 150.50)", input_filter='float', multiline=False, size_hint_y=None, height=dp(40))
        
        spin_cat = Spinner(text=cats_desp[0] if cats_desp else 'Outros', values=cats_desp, size_hint_y=None, height=dp(45), background_color=(0.3, 0.3, 0.3, 1))
        ent_meses = TextInput(text="1", hint_text="Parcelas", input_filter='int', multiline=False, size_hint_y=None, height=dp(40))
        
        btn_venc = BotaoData(size_hint_y=None, height=dp(45))

        def mudar_tipo(spinner, text):
            if text == 'Renda':
                spinner_cat.values = cats_ren
                spinner_cat.text = cats_ren[0] if cats_ren else 'Outros'
                btn_venc.disabled = True
            else:
                spinner_cat.values = cats_desp
                spinner_cat.text = cats_desp[0] if cats_desp else 'Outros'
                btn_venc.disabled = False

        spin_tipo.bind(text=mudar_tipo)
        spinner_cat = spin_cat

        btn_salvar = Button(text="SALVAR", size_hint_y=None, height=dp(50), background_color=(0.1, 0.6, 0.3, 1), bold=True)

        content.add_widget(Label(text="Nova Transação", bold=True, size_hint_y=None, height=dp(30), font_size='18sp'))
        content.add_widget(spin_tipo)
        content.add_widget(ent_desc)
        content.add_widget(ent_val)
        content.add_widget(spinner_cat)
        content.add_widget(ent_meses)
        content.add_widget(Label(text="Data de Vencimento:", size_hint_y=None, height=dp(20), halign="left"))
        content.add_widget(btn_venc)
        content.add_widget(btn_salvar)

        popup = Popup(title="Adicionar", content=content, size_hint=(0.95, 0.9))

        def salvar(instance):
            desc = ent_desc.text.strip()
            v_txt = ent_val.text.strip()
            tipo = spin_tipo.text.lower()
            cat = spinner_cat.text
            meses = int(ent_meses.text) if ent_meses.text else 1
            venc_br = btn_venc.text

            if not desc or not v_txt: return

            try:
                valor = float(v_txt.replace(",", "."))
                data_ini = datetime.now()
                venc_ini = None
                if venc_br and tipo == 'despesa':
                    venc_ini = datetime.strptime(venc_br, "%d/%m/%Y")

                con = conectar(); cur = con.cursor()

                for i in range(meses):
                    mes_total = data_ini.month - 1 + i
                    ano_parcela = data_ini.year + mes_total // 12
                    mes_parcela = mes_total % 12 + 1
                    
                    ultimo_dia = calendar.monthrange(ano_parcela, mes_parcela)[1]
                    dia_parcela = min(data_ini.day, ultimo_dia)
                    data_parcela = data_ini.replace(year=ano_parcela, month=mes_parcela, day=dia_parcela)
                    data_str = data_parcela.strftime("%Y-%m-%d")
                    
                    venc_str = None
                    if venc_ini:
                        ultimo_dia_venc = calendar.monthrange(ano_parcela, mes_parcela)[1]
                        venc_parcela = venc_ini.replace(year=ano_parcela, month=mes_parcela, day=min(venc_ini.day, ultimo_dia_venc))
                        venc_str = venc_parcela.strftime("%Y-%m-%d")

                    desc_final = f"{desc} ({i+1}/{meses})" if meses > 1 else desc

                    cur.execute("""INSERT INTO transacoes (descricao, valor, tipo, categoria, data, data_vencimento, usuario) 
                                   VALUES (?,?,?,?,?,?,?)""", (desc_final, valor, tipo, cat, data_str, venc_str, user))
                
                con.commit(); con.close(); popup.dismiss(); self.show_dashboard() 
            except Exception as e:
                print("Erro ao salvar:", e)

        btn_salvar.bind(on_press=salvar)
        popup.open()

class FinancasApp(App):
    usuario_atual = None
    def build(self):
        self.title = "Minhas Finanças Mobile"
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == "__main__":
    init_db()
    FinancasApp().run()
