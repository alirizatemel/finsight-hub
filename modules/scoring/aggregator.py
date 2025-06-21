from modules.scoring.beneish import BeneishScorer
from modules.scoring.graham import GrahamScorer
from modules.scoring.lynch import LynchScorer
from modules.scoring.piotroski import PiotroskiScorer


class ScoreAggregator:
    def __init__(self, company, row, balance, income, cashflow, curr, prev):
        self.company = company
        self.row = row
        self.balance = balance
        self.income = income
        self.cashflow = cashflow
        self.curr = curr
        self.prev = prev

    def run_all(self):
        piotroski = PiotroskiScorer(self.row, self.balance, self.income, self.curr, self.prev)
        beneish = BeneishScorer(self.company, self.balance, self.income, self.cashflow, self.curr, self.prev)
        graham = GrahamScorer(self.row)
        lynch = LynchScorer(self.row)

        f_score, f_summary, f_detail = piotroski.calculate()
        m_score, m_summary, m_lines = beneish.calculate()
        g_score, g_summary, g_lines = graham.calculate()
        l_score, l_summary, l_lines = lynch.calculate()

        return {
            "f_score": f_score,
            "f_karne": f_summary,
            "f_detail": f_detail,
            "m_skor": m_score,
            "m_karne": m_summary,
            "m_lines": m_lines,
            "graham_skor": g_score,
            "graham_karne": g_summary,
            "graham_lines": g_lines,
            "lynch_skor": l_score,
            "lynch_karne": l_summary,
            "lynch_lines": l_lines,
        }