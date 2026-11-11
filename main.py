from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDFloatingActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.checkbox import MDCheckbox
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.metrics import dp
from kivy.utils import platform
from kivy.clock import Clock
from datetime import datetime, timedelta
import sqlite3
import os
import calendar

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

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20), pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(0.9, 0.6))
        
        layout.add_widget(MDLabel(text="Finanças Mobile", font_style="H3", halign="center", theme_text_color="Primary"))
        layout.add_widget(MDLabel(text="Quem está acessando?", halign="center"))

        btn_jackson = MDRaisedButton(text="Jackson", size_hint_y=None, height=dp(60), pos_hint={"center_x": 0.5})
        btn_jackson.bind(on_release=lambda x: self.login("Jackson"))
        layout.add_widget(btn_jackson)

        btn_elcione = MDRaisedButton(text="Elcione", size_hint_y=None, height=dp(60), pos_hint={"center_x": 0.5})
        btn_elcione.bind(on_release=lambda x: self.login("Elcione"))
        layout.add_widget(btn_elcione)
        
        self.add_widget(layout)

    def login(self, usuario):
        self.manager.get_screen('main').usuario_atual = usuario
        self.manager.current = 'main'
        self.manager.get_screen('main').atualizar_tudo()

class MainScreen(MDScreen):
    usuario_atual = None
    mes_selecionado = datetime.now().strftime("%Y-%m")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(title="Início", elevation=4)
        self.layout.add_widget(self.toolbar)
        
        # Área de Conteúdo
        self.content = MDBoxLayout(orientation='vertical', padding=dp(10))
        self.layout.add_widget(self.content)
        
        # Menu Inferior
        nav = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5), padding=dp(5))
        btn_dash = MDFlatButton(text="Início", on_release=self.show_dashboard)
        btn_trans = MDFlatButton(text="Contas", on_release=self.show_transacoes)
        btn_add = MDFloatingActionButton(icon="plus", on_release=self.popup_nova_transacao)
        btn_metas = MDFlatButton(text="Metas", on_release=self.show_metas)
        btn_cat = MDFlatButton(text="Categorias", on_release=self.show_categorias)
        
        nav.add_widget(btn_dash)
        nav.add_widget(btn_trans)
        nav.add_widget(btn_add)
        nav.add_widget(btn_metas)
        nav.add_widget(btn_cat)
        self.layout.add_widget(nav)
        
        self.add_widget(self.layout)

    def atualizar_tudo(self):
        self.show_dashboard()

    def mudar_mes(self, spinner, text):
        mes, ano = text.split("/")
        self.mes_selecionado = f"{ano}-{mes}"
        self.show_dashboard()

    def show_dashboard(self, instance=None):
        self.content.clear_widgets()
        self.toolbar.title = f"Olá, {self.usuario_atual}!"
        
        con = conectar(); cur = con.cursor()
        
        query_renda = """SELECT COALESCE(SUM(valor),0) FROM transacoes 
                         WHERE tipo='renda' AND usuario=? 
                         AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ?"""
        cur.execute(query_renda, (self.usuario_atual, f"{self.mes_selecionado}%"))
        renda = cur.fetchone()[0]
        
        query_despesa = """SELECT COALESCE(SUM(valor),0) FROM transacoes 
                           WHERE tipo='despesa' AND usuario=? 
                           AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ?"""
        cur.execute(query_despesa, (self.usuario_atual, f"{self.mes_selecionado}%"))
        despesa = cur.fetchone()[0]
        con.close()

        saldo = renda - despesa

        scroll = MDScrollView()
        dash = MDBoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, padding=dp(5))
        dash.bind(minimum_height=dash.setter('height'))
        
        # Filtro de Mês
        meses = []
        for i in range(-12, 13):
            d = datetime.now().replace(day=1) + timedelta(days=32*i)
            meses.append(d.strftime("%m/%Y"))
        
        spinner_mes = MDSpinner(text=datetime.strptime(self.mes_selecionado, "%Y-%m").strftime("%m/%Y"), 
                              values=meses, size_hint=(None, None), size=(dp(150), dp(48)), pos_hint={"center_x": 0.5})
        spinner_mes.bind(text=self.mudar_mes)
        dash.add_widget(spinner_mes)

        # Cards
        dash.add_widget(self.criar_card("Renda do Mês", formatar_moeda(renda), (0.1, 0.4, 0.2, 1), (0.3, 1, 0.5, 1)))
        dash.add_widget(self.criar_card("Despesas do Mês", formatar_moeda(despesa), (0.4, 0.1, 0.1, 1), (1, 0.4, 0.4, 1)))
        dash.add_widget(self.criar_card("Saldo do Mês", formatar_moeda(saldo), (0.1, 0.2, 0.4, 1), (0.4, 0.7, 1, 1)))
        
        scroll.add_widget(dash)
        self.content.add_widget(scroll)

    def criar_card(self, titulo, valor, cor_fundo, cor_texto):
        card = MDCard(orientation='vertical', size_hint_y=None, height=dp(110), padding=dp(15), spacing=dp(5), md_bg_color=cor_fundo, radius=[dp(10)])
        card.add_widget(MDLabel(text=titulo, theme_text_color="Custom", text_color=(0.8, 0.8, 0.8, 1), halign="left"))
        card.add_widget(MDLabel(text=valor, font_style="H5", theme_text_color="Custom", text_color=cor_texto, halign="left"))
        return card

    def show_transacoes(self, instance=None):
        self.content.clear_widgets()
        self.toolbar.title = "Contas do Mês"
        
        con = conectar(); cur = con.cursor()
        query = """SELECT id, descricao, valor, tipo, data, data_vencimento, pago 
                   FROM transacoes WHERE usuario=? 
                   AND (CASE WHEN data_vencimento IS NOT NULL AND data_vencimento != '' THEN data_vencimento ELSE data END) LIKE ? 
                   ORDER BY pago ASC, data DESC"""
        cur.execute(query, (self.usuario_atual, f"{self.mes_selecionado}%"))
        rows = cur.fetchall()
        con.close()

        scroll = MDScrollView()
        lista = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=dp(5))
        lista.bind(minimum_height=lista.setter('height'))

        for tid, desc, valor, tipo, data, venc, pago in rows:
            card = MDCard(orientation='horizontal', size_hint_y=None, height=dp(70), padding=dp(10), radius=[dp(8)])
            cor_txt = (0.3, 1, 0.5, 1) if tipo == 'renda' else (1, 0.4, 0.4, 1)
            if pago: cor_txt = (0.5, 0.5, 0.5, 1)

            info = MDBoxLayout(orientation='vertical')
            info.add_widget(MDLabel(text=desc, theme_text_color="Custom", text_color=cor_txt, bold=True))
            texto_data = f"Venc: {venc[8:10]}/{venc[5:7]}" if venc else f"Data: {data[8:10]}/{data[5:7]}"
            if pago: texto_data += " (PAGO)"
            info.add_widget(MDLabel(text=texto_data, font_style="Caption", theme_text_color="Secondary"))
            
            card.add_widget(info)
            card.add_widget(MDLabel(text=formatar_moeda(valor), theme_text_color="Custom", text_color=cor_txt, bold=True))

            if not pago and tipo == 'despesa':
                btn_pagar = MDRaisedButton(text="Pagar", size_hint_x=None, width=dp(70), on_release=lambda x, i=tid: self.marcar_pago(i))
                card.add_widget(btn_pagar)

            lista.add_widget(card)

        scroll.add_widget(lista)
        self.content.add_widget(scroll)

    def marcar_pago(self, tid):
        con = conectar()
        con.execute("UPDATE transacoes SET pago=1 WHERE id=?", (tid,))
        con.commit(); con.close()
        self.show_transacoes()

    def show_metas(self, instance=None):
        self.content.clear_widgets()
        self.toolbar.title = "Metas"
        
        con = conectar(); cur = con.cursor()
        cur.execute("SELECT id, descricao, valor_alvo, valor_atual FROM metas WHERE usuario=?", (self.usuario_atual,))
        metas = cur.fetchall(); con.close()

        scroll = MDScrollView()
        lista = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        lista.bind(minimum_height=lista.setter('height'))

        btn_nova = MDRaisedButton(text="Nova Meta", size_hint_y=None, height=dp(50), pos_hint={"center_x": 0.5})
        btn_nova.bind(on_release=self.popup_nova_meta)
        lista.add_widget(btn_nova)

        for mid, desc, alvo, atual in metas:
            prog = min(atual / alvo, 1.0) if alvo > 0 else 0
            card = MDCard(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10), radius=[dp(8)])
            card.add_widget(MDLabel(text=desc, font_style="H6"))
            card.add_widget(MDLabel(text=f"{formatar_moeda(atual)} de {formatar_moeda(alvo)} ({prog*100:.0f}%)"))
            btn_guardar = MDRaisedButton(text="Guardar", on_release=lambda x, i=mid, a=atual: self.popup_guardar_meta(i, a))
            card.add_widget(btn_guardar)
            lista.add_widget(card)
        scroll.add_widget(lista)
        self.content.add_widget(scroll)

    def popup_guardar_meta(self, mid, atual):
        content = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(150))
        ent = MDTextField(hint_text="Valor (R$)", input_filter='float')
        content.add_widget(ent)
        
        dialog = MDDialog(title="Guardar Dinheiro", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: dialog.dismiss()),
                                   MDRaisedButton(text="SALVAR", on_release=lambda x: salvar(ent.text, dialog))])
        
        def salvar(texto, d):
            try:
                val = float(texto.replace(",", "."))
                con = conectar(); con.execute("UPDATE metas SET valor_atual=? WHERE id=?", (atual + val, mid))
                con.commit(); con.close(); d.dismiss(); self.show_metas()
            except: pass
        dialog.open()

    def popup_nova_meta(self, instance):
        content = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(200))
        ent_desc = MDTextField(hint_text="Ex: Viagem")
        ent_val = MDTextField(hint_text="Valor Alvo (R$)", input_filter='float')
        content.add_widget(ent_desc); content.add_widget(ent_val)
        
        dialog = MDDialog(title="Nova Meta", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: dialog.dismiss()),
                                   MDRaisedButton(text="CRIAR", on_release=lambda x: salvar(ent_desc.text, ent_val.text, dialog))])
        
        def salvar(desc, val_txt, d):
            try:
                val = float(val_txt.replace(",", "."))
                con = conectar(); con.execute("INSERT INTO metas (descricao, valor_alvo, usuario) VALUES (?,?,?)", 
                            (desc, val, self.usuario_atual))
                con.commit(); con.close(); d.dismiss(); self.show_metas()
            except: pass
        dialog.open()

    def show_categorias(self, instance=None):
        self.content.clear_widgets()
        self.toolbar.title = "Categorias"
        
        layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        form = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        ent_nome = MDTextField(hint_text="Nova Categoria")
        spin_tipo = MDSpinner(text='Despesa', values=('Despesa', 'Renda'))
        
        def adicionar(instance):
            nome = ent_nome.text.strip()
            tipo = 'despesa' if spin_tipo.text == 'Despesa' else 'renda'
            if nome:
                con = conectar()
                con.execute("INSERT INTO categorias (nome, tipo, usuario) VALUES (?,?,?)", (nome, tipo, self.usuario_atual))
                con.commit(); con.close()
                self.show_categorias()
                
        btn_add = MDRaisedButton(text="+", size_hint_x=None, width=dp(60), on_release=adicionar)
        
        form.add_widget(ent_nome)
        form.add_widget(spin_tipo)
        form.add_widget(btn_add)
        layout.add_widget(form)

        scroll = MDScrollView()
        lista = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        lista.bind(minimum_height=lista.setter('height'))
        
        con = conectar(); cur = con.cursor()
        cur.execute("SELECT id, nome, tipo FROM categorias WHERE usuario=? ORDER BY tipo, nome", (self.usuario_atual,))
        cats = cur.fetchall(); con.close()
        
        for cid, nome, tipo in cats:
            linha = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            cor = (1, 0.4, 0.4, 1) if tipo == 'despesa' else (0.3, 1, 0.5, 1)
            linha.add_widget(MDLabel(text=f"{nome} ({tipo.capitalize()})", theme_text_color="Custom", text_color=cor))
            
            def excluir(instance, c_id=cid):
                con = conectar()
                con.execute("DELETE FROM categorias WHERE id=?", (c_id,))
                con.commit(); con.close()
                self.show_categorias()

            btn_del = MDRaisedButton(text="X", size_hint_x=None, width=dp(50), on_release=excluir)
            linha.add_widget(btn_del)
            lista.add_widget(linha)
            
        scroll.add_widget(lista)
        layout.add_widget(scroll)
        self.content.add_widget(layout)

    def popup_nova_transacao(self, instance):
        con = conectar(); cur = con.cursor()
        cur.execute("SELECT nome FROM categorias WHERE tipo='despesa' AND usuario=?", (self.usuario_atual,))
        cats_desp = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT nome FROM categorias WHERE tipo='renda' AND usuario=?", (self.usuario_atual,))
        cats_ren = [r[0] for r in cur.fetchall()]
        con.close()

        content = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None, height=dp(400))
        
        spin_tipo = MDSpinner(text='Despesa', values=('Despesa', 'Renda'))
        ent_desc = MDTextField(hint_text="Descrição (Ex: Mercado)")
        ent_val = MDTextField(hint_text="Valor (Ex: 150.50)", input_filter='float')
        spin_cat = MDSpinner(text=cats_desp[0] if cats_desp else 'Outros', values=cats_desp)
        
        box_meses = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        ent_meses = MDTextField(text="1", hint_text="Meses", input_filter='int', size_hint_x=0.3)
        chk_fixa = MDCheckbox(size_hint_x=0.1)
        
        def toggle_fixa(cb, value):
            if value:
                ent_meses.text = "12"
                ent_meses.disabled = True
            else:
                ent_meses.text = "1"
                ent_meses.disabled = False
                
        chk_fixa.bind(active=toggle_fixa)
        box_meses.add_widget(ent_meses)
        box_meses.add_widget(MDLabel(text="Fixa/Recorrente", size_hint_x=0.6))
        box_meses.add_widget(chk_fixa)

        def mudar_tipo(spinner, text):
            if text == 'Renda':
                spinner_cat.values = cats_ren
                spinner_cat.text = cats_ren[0] if cats_ren else 'Outros'
            else:
                spinner_cat.values = cats_desp
                spinner_cat.text = cats_desp[0] if cats_desp else 'Outros'

        spin_tipo.bind(text=mudar_tipo)
        spinner_cat = spin_cat

        content.add_widget(spin_tipo)
        content.add_widget(ent_desc)
        content.add_widget(ent_val)
        content.add_widget(spinner_cat)
        content.add_widget(box_meses)

        dialog = MDDialog(title="Nova Transação", type="custom", content_cls=content,
                          buttons=[MDFlatButton(text="CANCELAR", on_release=lambda x: dialog.dismiss()),
                                   MDRaisedButton(text="SALVAR", on_release=lambda x: salvar())])

        def salvar():
            desc = ent_desc.text.strip()
            v_txt = ent_val.text.strip()
            tipo = spin_tipo.text.lower()
            cat = spinner_cat.text
            meses = int(ent_meses.text) if ent_meses.text else 1

            if not desc or not v_txt: return

            try:
                valor = float(v_txt.replace(",", "."))
                data_ini = datetime.now()
                con = conectar(); cur = con.cursor()

                for i in range(meses):
                    mes_total = data_ini.month - 1 + i
                    ano_parcela = data_ini.year + mes_total // 12
                    mes_parcela = mes_total % 12 + 1
                    
                    ultimo_dia = calendar.monthrange(ano_parcela, mes_parcela)[1]
                    dia_parcela = min(data_ini.day, ultimo_dia)
                    data_parcela = data_ini.replace(year=ano_parcela, month=mes_parcela, day=dia_parcela)
                    data_str = data_parcela.strftime("%Y-%m-%d")
                    
                    desc_final = f"{desc} ({i+1}/{meses})" if meses > 1 else desc

                    cur.execute("""INSERT INTO transacoes (descricao, valor, tipo, categoria, data, usuario) 
                                   VALUES (?,?,?,?,?,?)""", (desc_final, valor, tipo, cat, data_str, self.usuario_atual))
                
                con.commit(); con.close(); dialog.dismiss(); self.show_dashboard() 
            except Exception as e:
                print("Erro ao salvar:", e)

        dialog.open()

class FinancasApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        
        sm = MDScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == "__main__":
    init_db()
    FinancasApp().run()
