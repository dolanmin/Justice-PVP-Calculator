import math
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import json
import os

class JusticeCalculator:
    def __init__(self):
        self.BASE_COEFF = 2273 
        self.SCALING_COEFF = 1.0
        self.DEF_CONST = 10552
        self.RES_CONST = 1965
        
    def calculate_damage(self, attacker, defender, skill_percent=1.0):
        rem_def = max(0, defender['defense'] - attacker['break_def'])
        def_reduction = rem_def / (rem_def + self.DEF_CONST)
        
        rem_res = max(0, defender['element_res'] - attacker['ignore_res'])
        res_reduction = rem_res / (rem_res + self.RES_CONST)
        
        shield = defender['shield']
        break_shield = attacker['break_shield']
        if break_shield >= shield:
            rem_shield = 0
        elif break_shield >= shield / 3:
            rem_shield = 0.5 * (shield - break_shield)
        else:
            rem_shield = shield - 2 * break_shield
        rem_shield = max(0, rem_shield)
            
        atk_part = (attacker['attack'] - rem_shield + 
                    (attacker['kezhi'] + attacker['skill_enhance']) - 
                    (defender['resist'] + defender['skill_resist']))
        
        phy_base = self.BASE_COEFF + self.SCALING_COEFF * atk_part
        if phy_base < 0: phy_base = 0
        phy_final = phy_base * (1 - def_reduction)
        ele_final = self.SCALING_COEFF * attacker['element_attack'] * (1 - res_reduction)
        
        base_dmg = (phy_final + ele_final) * skill_percent
        
        multiplier = 1 + attacker['kezhi_pct'] - defender['perma_reduction']
        multiplier = max(0, multiplier)
        non_crit_damage = base_dmg * multiplier
        
        hit_diff = attacker['hit'] - defender['block']
        denom = hit_diff + 5950
        if denom == 0: denom = 0.001
        hit_rate_raw = 0.95 + (1.43 * hit_diff) / denom
        hit_rate = max(0.05, min(1.0, hit_rate_raw))
        
        rem_crit = attacker['crit'] - defender['crit_resist']
        if rem_crit <= -1548:
            crit_val = 0
        else:
            crit_val = (115 * rem_crit - 1230) / (rem_crit + 1548)
        crit_rate = (crit_val / 100.0) + attacker['extra_crit_rate']
        crit_rate = max(0.05, min(1.0, crit_rate))
        
        eff_crit_dmg = (1 + attacker['crit_dmg_bonus']) - defender['crit_def']
        eff_crit_dmg = max(1.0, eff_crit_dmg)
        
        crit_dmg_val = non_crit_damage * eff_crit_dmg
        exp_dmg = non_crit_damage * (1 + crit_rate * (eff_crit_dmg - 1)) * hit_rate
        
        return {
            "non_crit": non_crit_damage,
            "crit_val": crit_dmg_val,
            "expected": exp_dmg,
            "details": {
                "rem_def": rem_def,
                "rem_shield": rem_shield,
                "atk_part": atk_part,
                "def_red": def_reduction,
                "hit": hit_rate,
                "crit": crit_rate,
                "rem_res": rem_res
            }
        }

    def get_offensive_suggestions(self, attacker, defender, skill_pct):
        try:
            base = self.calculate_damage(attacker, defender, skill_pct)['expected']
            if base <= 0: return []
            suggestions = []
            attrs = [("攻擊", "attack"), ("破防", "break_def"), ("元素", "element_attack"), 
                     ("命中", "hit"), ("會心", "crit"), ("克制", "kezhi")]
            for name, key in attrs:
                new_atk = attacker.copy()
                new_atk[key] += 100
                d_new = self.calculate_damage(new_atk, defender, skill_pct)['expected']
                gain = (d_new - base) / base
                suggestions.append((name, gain))
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return suggestions
        except:
            return []

    def get_defensive_suggestions(self, attacker, defender, skill_pct):
        try:
            base = self.calculate_damage(attacker, defender, skill_pct)['expected']
            if base <= 0: return []
            suggestions = []
            attrs = [("防禦", "defense"), ("氣盾", "shield"), ("元抗", "element_res"), 
                     ("抵禦", "resist"), ("格擋", "block"), ("會抗", "crit_resist")]
            for name, key in attrs:
                new_def = defender.copy()
                new_def[key] += 100
                d_new = self.calculate_damage(attacker, new_def, skill_pct)['expected']
                reduction = (base - d_new) / base
                suggestions.append((name, reduction))
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return suggestions
        except:
            return []

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("逆水寒 PVP 傷害分析器 V5.2")
        self.geometry("1100x900")
        self.configure(bg="#f2f2f2")
        
        self.SAVE_FILE = "justice_save.json"
        self.saved_data = self.load_settings()
        
        self.calculator = JusticeCalculator()
        
        header = tk.Label(self, text="⚔️ PVP 傷害數據中心", font=('微軟正黑體', 18, 'bold'), bg="#2d3436", fg="#ffffff", pady=10)
        header.pack(side=tk.TOP, fill=tk.X)
        
        footer_frame = tk.Frame(self, bg="#e0e0e0", bd=1, relief="sunken")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("系統準備就緒 (已載入設定)")
        status_bar = tk.Label(footer_frame, textvariable=self.status_var, font=('微軟正黑體', 9), fg="#666666", bg="#e0e0e0", padx=10, pady=5)
        status_bar.pack(side=tk.LEFT)

        author_label = tk.Label(footer_frame, text="Designed by 由那由它", font=('微軟正黑體', 9, 'bold'), fg="#555555", bg="#e0e0e0", padx=10, pady=5)
        author_label.pack(side=tk.RIGHT)

        main_frame = tk.Frame(self, bg="#f2f2f2")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        input_container = tk.Frame(main_frame, bg="#f2f2f2")
        input_container.pack(fill=tk.X, pady=5)
        
        self.atk_entries = {}
        left_box = tk.LabelFrame(input_container, text="【攻擊方數據】", font=('微軟正黑體', 12, 'bold'), 
                                 bg="#fff0f0", fg="#c0392b", padx=10, pady=10)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.def_entries = {}
        right_box = tk.LabelFrame(input_container, text="【防禦方數據】", font=('微軟正黑體', 12, 'bold'), 
                                  bg="#f0f8ff", fg="#2980b9", padx=10, pady=10)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        atk_fields = [
            ("攻擊力", "attack", "11194"), 
            ("破防", "break_def", "9000"),
            ("破盾", "break_shield", "349"), 
            ("元素攻擊", "element_attack", "3600"),
            ("克制數值", "kezhi", "4000"), 
            ("技能增強", "skill_enhance", "0"),
            ("命中", "hit", "2300"), 
            ("會心", "crit", "4500"),
            ("會傷加成 (如0.713)", "crit_dmg_bonus", "0.713"), 
            ("額外會心 (如0.05)", "extra_crit_rate", "0.05"),
            ("克制強度 (如0.161)", "kezhi_pct", "0.161"), 
            ("忽視元抗", "ignore_res", "2000"),
            ("技能倍率 (如100)", "skill_pct", "100")
        ]
        
        def_fields = [
            ("防禦力", "defense", "9800"), 
            ("氣盾", "shield", "2000"),
            ("元素抗性", "element_res", "2500"), 
            ("抵御", "resist", "4500"),
            ("格擋", "block", "2000"), 
            ("會心抵抗", "crit_resist", "2700"),
            ("常駐減傷 (如0.25)", "perma_reduction", "0.25"), 
            ("技能抵御", "skill_resist", "200"),
            ("會心防禦 (如0.10)", "crit_def", "0.1"), 
            ("敵人血量", "hp", "260000")
        ]
        
        self.create_inputs_grid(left_box, atk_fields, self.atk_entries, "#fff0f0")
        self.create_inputs_grid(right_box, def_fields, self.def_entries, "#f0f8ff")
        
        calc_btn = tk.Button(main_frame, text="🚀 執行全面分析 (並存檔)", font=('微軟正黑體', 14, 'bold'), 
                             bg="#27ae60", fg="white", cursor="hand2", width=20, pady=5, command=self.on_calculate)
        calc_btn.pack(pady=10)
        
        result_box = tk.LabelFrame(main_frame, text="【分析報告】", font=('微軟正黑體', 12, 'bold'), 
                                   bg="#ffffff", fg="#333333", padx=10, pady=10)
        result_box.pack(fill=tk.BOTH, expand=True)
        
        dmg_frame = tk.Frame(result_box, bg="#fffcf5")
        dmg_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dmg_labels = {}
        for title, color in [("白字傷害", "#7f8c8d"), ("黃字傷害", "#e67e22"), ("期望傷害", "#d35400")]:
            f = tk.Frame(dmg_frame, bg="#fffcf5", pady=5)
            f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tk.Label(f, text=title, font=('微軟正黑體', 11), bg="#fffcf5", fg="#7f8c8d").pack()
            l = tk.Label(f, text="---", font=('Arial', 24, 'bold'), bg="#fffcf5", fg=color)
            l.pack()
            self.dmg_labels[title] = l

        grid_frame = tk.Frame(result_box, bg="white")
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        grid_frame.columnconfigure(0, weight=4)
        grid_frame.columnconfigure(1, weight=6)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.rowconfigure(1, weight=1)

        text_config = {
            "padx": 10, "pady": 10, "spacing1": 5, "spacing2": 3, 
            "relief": "flat", "highlightthickness": 1, "highlightbackground": "#cccccc"
        }

        self.detail_text = tk.Text(grid_frame, font=('微軟正黑體', 11), bg="#f9f9f9", **text_config)
        self.detail_text.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        self.detail_text.insert(tk.END, "等待計算...\n\n(點擊上方按鈕開始)")
        self.detail_text.config(state="disabled")

        self.atk_text = tk.Text(grid_frame, font=('微軟正黑體', 10), bg="#fff5f5", height=8, **text_config)
        self.atk_text.grid(row=0, column=1, sticky="nsew", pady=(0, 2))
        self.atk_text.insert(tk.END, "攻擊收益建議區")
        self.atk_text.config(state="disabled")

        self.def_text = tk.Text(grid_frame, font=('微軟正黑體', 10), bg="#f0faff", height=8, **text_config)
        self.def_text.grid(row=1, column=1, sticky="nsew", pady=(2, 0))
        self.def_text.insert(tk.END, "防禦收益建議區")
        self.def_text.config(state="disabled")

    def load_settings(self):
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(self):
        data = {}
        for key, entry in self.atk_entries.items():
            data[key] = entry.get()
        for key, entry in self.def_entries.items():
            data[key] = entry.get()
        try:
            with open(self.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("存檔失敗", f"無法儲存設定：{e}")

    def create_inputs_grid(self, parent, fields, entry_dict, bg_color):
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)
        for i, (text, key, default_val) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            val = self.saved_data.get(key, default_val)
            tk.Label(parent, text=text, font=('微軟正黑體', 10), bg=bg_color).grid(row=row, column=col, sticky="w", pady=4, padx=(5, 2))
            ent = tk.Entry(parent, width=10, font=('Arial', 10), relief="solid", bd=1)
            ent.insert(0, val)
            ent.grid(row=row, column=col+1, sticky="w", pady=4, padx=(0, 15))
            entry_dict[key] = ent

    def on_calculate(self):
        self.status_var.set("正在計算並存檔...")
        self.update_idletasks()
        
        try:
            atk = {k: float(v.get()) for k, v in self.atk_entries.items() if k != 'skill_pct'}
            defn = {k: float(v.get()) for k, v in self.def_entries.items() if k != 'hp'}
            skill_pct = float(self.atk_entries['skill_pct'].get()) / 100.0
            enemy_hp = float(self.def_entries['hp'].get())
            
            self.save_settings()
            
            res = self.calculator.calculate_damage(atk, defn, skill_pct)
            atk_suggs = self.calculator.get_offensive_suggestions(atk, defn, skill_pct)
            def_suggs = self.calculator.get_defensive_suggestions(atk, defn, skill_pct)
            
            exp_dmg = res['expected']
            hits_to_kill = math.ceil(enemy_hp / exp_dmg) if exp_dmg > 0 else "∞"
            
            self.dmg_labels["白字傷害"].config(text=f"{int(res['non_crit']):,}")
            self.dmg_labels["黃字傷害"].config(text=f"{int(res['crit_val']):,}")
            self.dmg_labels["期望傷害"].config(text=f"{int(res['expected']):,}")
            
            detail_txt = (
                f"【實戰數據】\n"
                f"● 擊殺所需: {hits_to_kill} 刀\n"
                f"● 實際命中: {res['details']['hit']:.1%}\n"
                f"● 實際會心: {res['details']['crit']:.1%}\n\n"
                f"【詳細過程】\n"
                f"● 有效攻擊: {int(res['details']['atk_part']):,}\n"
                f"● 剩餘防禦: {int(res['details']['rem_def'])}\n"
                f"● 剩餘氣盾: {int(res['details']['rem_shield'])}\n"
                f"● 剩餘元抗: {int(res['details']['rem_res'])}\n"
            )
            self.update_text_widget(self.detail_text, detail_txt)
            
            atk_txt = "【⚔️ 攻擊收益 / 每100點】\n"
            if atk_suggs:
                for i, (name, gain) in enumerate(atk_suggs[:5]):
                    icon = ["🥇", "🥈", "🥉"][i] if i < 3 else f" {i+1}."
                    atk_txt += f"{icon} {name}: +{gain:.2%}\n"
            else:
                atk_txt += "無有效建議"
            self.update_text_widget(self.atk_text, atk_txt)
            
            def_txt = "【🛡️ 防禦收益 / 每100點】\n"
            if def_suggs:
                for i, (name, red) in enumerate(def_suggs):
                    icon = ["🥇", "🥈", "🥉"][i] if i < 3 else f" {i+1}."
                    def_txt += f"{icon} {name}: 減傷 {red:.2%}\n"
            else:
                def_txt += "無有效建議"
            self.update_text_widget(self.def_text, def_txt)
            
            self.status_var.set("計算完成 (設定已儲存)")
            
        except Exception as e:
            error_msg = traceback.format_exc()
            self.status_var.set("計算錯誤")
            messagebox.showerror("錯誤", f"無法計算：\n{str(e)}")

    def update_text_widget(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()