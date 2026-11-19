import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

# ═══════════════════════════════════════════════════
#  МОДЕЛИ ДАННЫХ
# ═══════════════════════════════════════════════════
@dataclass
class Resource:
    id: int; name: str; category: str; r_type: str

@dataclass
class Operation:
    id: int; product_id: int; name: str; seq: int; dur: int
    worker_type: str; machine_type: Optional[str] = None

@dataclass
class Product:
    id: int; name: str

@dataclass
class Order:
    id: int; product_id: int; start_after: datetime; deadline: datetime; penalty: float = 100.0

@dataclass
class ScheduleItem:
    order_id: int; op_name: str; worker_name: str; machine_name: str; start: datetime; end: datetime

# ═══════════════════════════════════════════════════
#  МЕНЕДЖЕР ДАННЫХ И ЛОГИКА
# ═══════════════════════════════════════════════════
class DataManager:
    def __init__(self):
        self.resources, self.products, self.ops, self.orders, self.schedule = [], [], [], [], []
        self._ids = {"res": 1, "pt": 1, "op": 1, "ord": 1}

    def add_res(self, n, c, t):
        if not n or not c: return False
        self.resources.append(Resource(self._ids["res"], n, c, t))
        self._ids["res"] += 1; return True

    def add_prod(self, n):
        if not n: return None
        p = Product(self._ids["pt"], n)
        self.products.append(p); self._ids["pt"] += 1; return p

    def add_op(self, pid, n, dur, wt, mt):
        try:
            p_id, d = int(pid), int(dur) # Валидация типов данных[cite: 6]
            seq = len([o for o in self.ops if o.product_id == p_id]) + 1
            self.ops.append(Operation(self._ids["op"], p_id, n, seq, d, wt, mt if mt else None))
            self._ids["op"] += 1; return True
        except: return False

    def add_order(self, pid, s_str, d_str):
        try:
            p_id = int(pid)
            s = datetime.strptime(s_str, "%d.%m.%Y %H:%M")
            d = datetime.strptime(d_str, "%d.%m.%Y %H:%M")
            self.orders.append(Order(self._ids["ord"], p_id, s, d))
            self._ids["ord"] += 1; return True
        except: return False

    def build_schedule(self):
        self.schedule = []
        res_busy = {r.id: datetime.min for r in self.resources}
        # Алгоритм ASAP со сквозным поиском интервалов[cite: 2, 3]
        for order in sorted(self.orders, key=lambda x: x.deadline):
            ops = sorted([o for o in self.ops if o.product_id == order.product_id], key=lambda x: x.seq)
            last_end = order.start_after
            for op in ops:
                workers = [r for r in self.resources if r.category == "Сотрудник" and r.r_type == op.worker_type]
                machines = [r for r in self.resources if r.category == "Станок" and r.r_type == op.machine_type] if op.machine_type else [None]
                if not workers: continue 
                curr, found, limit = last_end, False, 0
                while not found and limit < 1000:
                    limit += 1
                    if curr.hour < 8: curr = curr.replace(hour=8, minute=0)
                    if curr.hour >= 16: curr = (curr + timedelta(days=1)).replace(hour=8, minute=0)
                    if curr + timedelta(minutes=op.dur) > curr.replace(hour=16, minute=0):
                        curr = (curr + timedelta(days=1)).replace(hour=8, minute=0); continue
                    for w in workers:
                        for m in machines:
                            m_f = res_busy[m.id] if m else datetime.min
                            if res_busy[w.id] <= curr and m_f <= curr:
                                start, end = curr, curr + timedelta(minutes=op.dur)
                                self.schedule.append(ScheduleItem(order.id, op.name, w.name, m.name if m else "-", start, end))
                                res_busy[w.id], last_end, found = end, end, True
                                if m: res_busy[m.id] = end
                                break
                        if found: break
                    if not found: curr += timedelta(minutes=15)

    def get_penalty(self):
        total = 0.0
        for o in self.orders:
            o_ends = [i.end for i in self.schedule if i.order_id == o.id]
            if o_ends and max(o_ends) > o.deadline:
                total += (max(o_ends) - o.deadline).total_seconds() / 3600 * o.penalty
        return round(total, 2)

# ═══════════════════════════════════════════════════
#  ИНТЕРФЕЙС (Задания №4-5)
# ═══════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("APS PRO | Производственное планирование")
        self.geometry("1100x800")
        self.dm = DataManager()
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.p1 = ResPage(nb, self.dm); nb.add(self.p1, text="1. Ресурсы")
        self.p2 = TechPage(nb, self.dm); nb.add(self.p2, text="2. Техпроцессы")
        self.p3 = OrderPage(nb, self.dm); nb.add(self.p3, text="3. Заказы")
        self.p4 = SchedPage(nb, self.dm); nb.add(self.p4, text="4. График")

class ResPage(tk.Frame):
    def __init__(self, p, dm):
        super().__init__(p)
        self.dm = dm
        f = tk.Frame(self); f.pack(pady=10)
        self.en, self.ec, self.et = tk.Entry(f), ttk.Combobox(f, values=["Сотрудник", "Станок"], state="readonly"), tk.Entry(f)
        for i, l in enumerate(["Имя:", "Категория:", "Спец/Тип:"]): tk.Label(f, text=l).grid(row=0, column=i*2)
        self.en.grid(row=0, column=1); self.ec.grid(row=0, column=3); self.et.grid(row=0, column=5)
        tk.Button(f, text="Добавить", command=self.add).grid(row=0, column=6, padx=10)
        self.tree = ttk.Treeview(self, columns=(1,2,3,4), show="headings")
        for i, h in enumerate(["ID", "Имя", "Категория", "Специализация"], 1): self.tree.heading(i, text=h)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add(self):
        if self.dm.add_res(self.en.get(), self.ec.get(), self.et.get()): self.refresh()
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.dm.resources: self.tree.insert("", "end", values=(r.id, r.name, r.category, r.r_type))

class TechPage(tk.Frame):
    def __init__(self, p, dm):
        super().__init__(p)
        self.dm = dm
        f1 = tk.LabelFrame(self, text="Шаг 1: Создать изделие"); f1.pack(fill="x", padx=10, pady=5)
        self.ep = tk.Entry(f1); self.ep.pack(side="left", padx=10, pady=10)
        tk.Button(f1, text="Создать", command=self.add_p).pack(side="left")
        f2 = tk.LabelFrame(self, text="Шаг 2: Добавить операцию в техпроцесс"); f2.pack(fill="x", padx=10, pady=5)
        self.epid, self.en, self.ed, self.ew, self.em = tk.Entry(f2, width=5), tk.Entry(f2), tk.Entry(f2, width=5), tk.Entry(f2), tk.Entry(f2)
        for i, (l, e) in enumerate([("PID", self.epid), ("Название", self.en), ("Мин", self.ed), ("Сотр", self.ew), ("Стан", self.em)]):
            tk.Label(f2, text=l).grid(row=0, column=i*2, padx=2); e.grid(row=0, column=i*2+1, padx=5, pady=10)
        tk.Button(f2, text="Добавить", command=self.add_o).grid(row=0, column=10, padx=10)
        self.tree = ttk.Treeview(self, columns=(1,2,3,4,5), show="headings")
        for i, h in enumerate(["PID", "№", "Операция", "Спец. сотр.", "Тип станка"], 1): self.tree.heading(i, text=h)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_p(self):
        if self.dm.add_prod(self.ep.get()): messagebox.showinfo("Успех", "Изделие зарегистрировано")
    def add_o(self):
        if self.dm.add_op(self.epid.get(), self.en.get(), self.ed.get(), self.ew.get(), self.em.get()): self.refresh()
        else: messagebox.showerror("Ошибка", "Проверьте PID (число) и длительность")
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for o in self.dm.ops: self.tree.insert("", "end", values=(o.product_id, o.seq, o.name, o.worker_type, o.machine_type if o.machine_type else "-"))

class OrderPage(tk.Frame):
    def __init__(self, p, dm):
        super().__init__(p)
        self.dm = dm
        f = tk.Frame(self); f.pack(pady=10)
        self.ei, self.es, self.ed = tk.Entry(f, width=5), tk.Entry(f), tk.Entry(f)
        self.es.insert(0, datetime.now().strftime("%d.%m.%Y 08:00"))
        self.ed.insert(0, (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y 16:00"))
        for i, (l, e) in enumerate([("PID изделия", self.ei), ("Старт после", self.es), ("Дедлайн", self.ed)]):
            tk.Label(f, text=l).grid(row=0, column=i*2); e.grid(row=0, column=i*2+1, padx=5)
        tk.Button(f, text="Разместить заказ", command=self.add).grid(row=0, column=6, padx=10)
        self.tree = ttk.Treeview(self, columns=(1,2,3,4), show="headings")
        for i, h in enumerate(["ID Заказа", "PID", "Начать после", "Крайний срок"], 1): self.tree.heading(i, text=h)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add(self):
        if self.dm.add_order(self.ei.get(), self.es.get(), self.ed.get()): self.refresh()
        else: messagebox.showerror("Ошибка", "Неверный формат даты или PID")
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for o in self.dm.orders: self.tree.insert("", "end", values=(o.id, o.product_id, o.start_after.strftime("%d.%m %H:%M"), o.deadline.strftime("%d.%m %H:%M")))

class SchedPage(tk.Frame):
    def __init__(self, p, dm):
        super().__init__(p)
        self.dm = dm
        tk.Button(self, text="🚀 СФОРМИРОВАТЬ РАСПИСАНИЕ (ASAP)", bg="#22c55e", fg="white", font=("Arial", 10, "bold"), command=self.run).pack(pady=15)
        self.lbl = tk.Label(self, text="Итоговые штрафы: 0.0 руб.", font=("Arial", 12, "bold"), fg="#ef4444"); self.lbl.pack()
        self.tree = ttk.Treeview(self, columns=(1,2,3,4,5,6), show="headings")
        for i, h in enumerate(["Заказ", "Операция", "Исполнитель", "Оборудование", "Начало", "Конец"], 1): self.tree.heading(i, text=h)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def run(self):
        self.dm.build_schedule()
        self.tree.delete(*self.tree.get_children())
        for i in self.dm.schedule:
            self.tree.insert("", "end", values=(f"#{i.order_id}", i.op_name, i.worker_name, i.machine_name, i.start.strftime("%d.%m %H:%M"), i.end.strftime("%d.%m %H:%M")))
        self.lbl.config(text=f"Итоговые штрафы: {self.dm.get_penalty()} руб.")

if __name__ == "__main__":
    App().mainloop()