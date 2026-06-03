# # option_chain_service.py - FIXED VERSION WITH DEBUG PRINTS
# import pandas as pd
# import numpy as np
# from datetime import datetime

# class OptionChainService:
#     def __init__(self, tsl):
#         self.tsl = tsl

#         self.INDEX_CONFIG = {
#             "NIFTY": {
#                 "api_name": "NIFTY",
#                 "display_name": "NIFTY 50",
#                 "exchange": "INDEX",
#                 "step": 50,
#                 "default_spot": 24500
#             },
#             "BANKNIFTY": {
#                 "api_name": "BANKNIFTY",
#                 "display_name": "BANKNIFTY",
#                 "exchange": "INDEX",
#                 "step": 100,
#                 "default_spot": 52000
#             },
#             "FINNIFTY": {
#                 "api_name": "FINNIFTY",
#                 "display_name": "FINNIFTY",
#                 "exchange": "INDEX",
#                 "step": 50,
#                 "default_spot": 23000
#             },
#             "SENSEX": {
#                 "api_name": "SENSEX",
#                 "display_name": "SENSEX",
#                 "exchange": "BSE",
#                 "step": 100,
#                 "default_spot": 80000
#             }
#         }

#     # ─────────────────────────────────────────────
#     # PUBLIC ENTRY POINT
#     # ─────────────────────────────────────────────
#     def get_option_chain(self, underlying="NIFTY", expiry_index=0, num_strikes=12):
#         """
#         Fetch live option chain from Dhan-Tradehull.
#         Falls back to synthetic data only when API fails.
#         """
#         config = self.INDEX_CONFIG.get(underlying, self.INDEX_CONFIG["NIFTY"])
#         api_name  = config["api_name"]
#         exchange  = config["exchange"]
#         step      = config["step"]

#         print(f"\n{'='*60}")
#         print(f"[OptionChain] Fetching: {underlying}  expiry={expiry_index}  strikes=±{num_strikes}")
#         print(f"[OptionChain] API name={api_name}  exchange={exchange}  step={step}")

#         # ── 1. Get spot price ────────────────────
#         spot_price = self._get_spot_price(api_name)
#         print(f"[OptionChain] Spot price for '{api_name}': {spot_price}")

#         if spot_price == 0:
#             spot_price = config["default_spot"]
#             print(f"[OptionChain] ⚠ Using default spot: {spot_price}")

#         # ── 2. Call Dhan option chain API ────────
#         try:
#             print(f"[OptionChain] Calling tsl.get_option_chain(Underlying='{api_name}', exchange='{exchange}', expiry={expiry_index}, num_strikes={num_strikes})")
#             oc_raw = self.tsl.get_option_chain(
#                 Underlying=api_name,
#                 exchange=exchange,
#                 expiry=expiry_index,
#                 num_strikes=num_strikes
#             )

#             # ── 3. Inspect the raw return ────────
#             print(f"[OptionChain] Raw return type : {type(oc_raw)}")

#             # Dhan-Tradehull sometimes returns a tuple: (df, metadata)
#             if isinstance(oc_raw, tuple):
#                 print(f"[OptionChain] Tuple length: {len(oc_raw)}")
#                 oc_df = oc_raw[0]          # first element is always the DataFrame
#             else:
#                 oc_df = oc_raw

#             if oc_df is None:
#                 print("[OptionChain] ✗ API returned None — falling back to synthetic data")
#                 return self._fallback(underlying, spot_price, num_strikes, step)

#             if not isinstance(oc_df, pd.DataFrame):
#                 print(f"[OptionChain] ✗ Not a DataFrame ({type(oc_df)}) — falling back")
#                 return self._fallback(underlying, spot_price, num_strikes, step)

#             if oc_df.empty:
#                 print("[OptionChain] ✗ Empty DataFrame — falling back")
#                 return self._fallback(underlying, spot_price, num_strikes, step)

#             # ── 4. Show what we got ──────────────
#             print(f"[OptionChain] ✓ DataFrame shape: {oc_df.shape}")
#             print(f"[OptionChain] Columns: {list(oc_df.columns)}")
#             print(f"[OptionChain] First 3 rows:\n{oc_df.head(3).to_string()}")

#             return self._format_live_chain(oc_df, underlying, spot_price, step)

#         except Exception as e:
#             import traceback
#             print(f"[OptionChain] ✗ Exception: {e}")
#             traceback.print_exc()
#             return self._fallback(underlying, spot_price, num_strikes, step)

#     # ─────────────────────────────────────────────
#     # SPOT PRICE
#     # ─────────────────────────────────────────────
#     def _get_spot_price(self, symbol):
#         """Try multiple Dhan-Tradehull methods to get LTP."""

#         # Method A: get_ltp_data (most reliable)
#         try:
#             ltp_data = self.tsl.get_ltp_data(names=[symbol])
#             print(f"[SpotPrice] get_ltp_data({symbol}) → {ltp_data}")
#             if ltp_data and symbol in ltp_data:
#                 val = ltp_data[symbol]
#                 if val and float(val) > 0:
#                     return float(val)
#         except Exception as e:
#             print(f"[SpotPrice] get_ltp_data failed: {e}")

#         # Method B: get_quote_data
#         try:
#             q = self.tsl.get_quote_data(names=[symbol])
#             print(f"[SpotPrice] get_quote_data({symbol}) → {q}")
#             if q and symbol in q:
#                 d = q[symbol]
#                 if isinstance(d, dict):
#                     ltp = d.get("last_price") or d.get("ltp") or d.get("close") or 0
#                     if ltp and float(ltp) > 0:
#                         return float(ltp)
#         except Exception as e:
#             print(f"[SpotPrice] get_quote_data failed: {e}")

#         # Method C: NIFTY 50 alias
#         if symbol == "NIFTY":
#             try:
#                 ltp_data = self.tsl.get_ltp_data(names=["NIFTY 50"])
#                 print(f"[SpotPrice] get_ltp_data('NIFTY 50') → {ltp_data}")
#                 if ltp_data and "NIFTY 50" in ltp_data:
#                     val = ltp_data["NIFTY 50"]
#                     if val and float(val) > 0:
#                         return float(val)
#             except Exception as e:
#                 print(f"[SpotPrice] NIFTY 50 alias failed: {e}")

#         return 0

#     # ─────────────────────────────────────────────
#     # FORMAT LIVE DATA
#     # ─────────────────────────────────────────────
#     def _format_live_chain(self, oc_df, underlying, spot_price, step):
#         """Parse the live DataFrame into the dashboard JSON format."""
#         config      = self.INDEX_CONFIG.get(underlying, self.INDEX_CONFIG["NIFTY"])
#         atm_strike  = round(spot_price / step) * step
#         strikes_data = []
#         total_ce_oi  = 0
#         total_pe_oi  = 0

#         # Normalise column names: strip spaces, lower
#         col_map = {c: c.strip() for c in oc_df.columns}
#         oc_df   = oc_df.rename(columns=col_map)

#         def _f(row, *keys, default=0.0):
#             """Try multiple key names, return float."""
#             for k in keys:
#                 v = row.get(k, None)
#                 if v is not None and v != "" and str(v) not in ("nan", "NaN"):
#                     try:
#                         return float(v)
#                     except Exception:
#                         pass
#             return default

#         def _i(row, *keys, default=0):
#             return int(_f(row, *keys, default=float(default)))

#         for _, row in oc_df.iterrows():
#             strike = _i(row, "Strike Price", "strike", "STRIKE", default=0)
#             if strike == 0:
#                 continue

#             ce_ltp       = _f(row, "CE LTP",      "CE_LTP",      "ce_ltp")
#             ce_oi        = _i(row, "CE OI",        "CE_OI",       "ce_oi")
#             ce_oi_change = _i(row, "CE Chg in OI", "CE_CHG_OI",   "ce_chg_in_oi")
#             ce_iv        = _f(row, "CE IV",        "CE_IV",       "ce_iv",   default=14.20)
#             ce_delta     = _f(row, "CE Delta",     "CE_DELTA",    "ce_delta")
#             ce_theta     = _f(row, "CE Theta",     "CE_THETA",    "ce_theta")
#             ce_gamma     = _f(row, "CE Gamma",     "CE_GAMMA",    "ce_gamma")
#             ce_vega      = _f(row, "CE Vega",      "CE_VEGA",     "ce_vega")

#             pe_ltp       = _f(row, "PE LTP",      "PE_LTP",      "pe_ltp")
#             pe_oi        = _i(row, "PE OI",        "PE_OI",       "pe_oi")
#             pe_oi_change = _i(row, "PE Chg in OI", "PE_CHG_OI",   "pe_chg_in_oi")
#             pe_iv        = _f(row, "PE IV",        "PE_IV",       "pe_iv",   default=14.20)
#             pe_delta     = _f(row, "PE Delta",     "PE_DELTA",    "pe_delta")
#             pe_theta     = _f(row, "PE Theta",     "PE_THETA",    "pe_theta")
#             pe_gamma     = _f(row, "PE Gamma",     "PE_GAMMA",    "pe_gamma")
#             pe_vega      = _f(row, "PE Vega",      "PE_VEGA",     "pe_vega")

#             # Fill missing LTPs with approximation
#             if ce_ltp == 0:
#                 dist = (atm_strike - strike) / step
#                 ce_ltp = max(0.05, dist * 10 + 5) if strike <= atm_strike else max(0.05, 30 + dist * 3)
#             if pe_ltp == 0:
#                 dist = (strike - atm_strike) / step
#                 pe_ltp = max(0.05, dist * 10 + 5) if strike >= atm_strike else max(0.05, 30 + dist * 3)

#             # Fill missing Greeks with approximations
#             gdist = abs(strike - atm_strike) / step
#             if ce_delta == 0:
#                 ce_delta = max(0.05, min(0.95, 0.5 - (strike - atm_strike) / (step * 4)))
#             if pe_delta == 0:
#                 pe_delta = -max(0.05, min(0.95, 0.5 + (strike - atm_strike) / (step * 4)))
#             if ce_theta == 0:
#                 ce_theta = round(-12 - gdist * 2, 2)
#             if pe_theta == 0:
#                 pe_theta = round(-12 - gdist * 2, 2)
#             if ce_gamma == 0:
#                 ce_gamma = round(max(0.0001, 0.003 - gdist * 0.0003), 5)
#             if pe_gamma == 0:
#                 pe_gamma = round(max(0.0001, 0.003 - gdist * 0.0003), 5)
#             if ce_vega == 0:
#                 ce_vega = round(max(2, 12 - gdist), 2)
#             if pe_vega == 0:
#                 pe_vega = round(max(2, 12 - gdist), 2)

#             total_ce_oi += ce_oi
#             total_pe_oi += pe_oi

#             strikes_data.append({
#                 "strike": strike,
#                 "ce": {
#                     "ltp":       round(ce_ltp, 2),
#                     "oi":        ce_oi,
#                     "oi_change": ce_oi_change,
#                     "iv":        round(ce_iv, 2),
#                     "delta":     round(ce_delta, 3),
#                     "theta":     round(ce_theta, 2),
#                     "gamma":     round(ce_gamma, 5),
#                     "vega":      round(ce_vega, 2),
#                     "signal":    self._signal(ce_oi_change)
#                 },
#                 "pe": {
#                     "ltp":       round(pe_ltp, 2),
#                     "oi":        pe_oi,
#                     "oi_change": pe_oi_change,
#                     "iv":        round(pe_iv, 2),
#                     "delta":     round(pe_delta, 3),
#                     "theta":     round(pe_theta, 2),
#                     "gamma":     round(pe_gamma, 5),
#                     "vega":      round(pe_vega, 2),
#                     "signal":    self._signal(pe_oi_change)
#                 }
#             })

#         if not strikes_data:
#             print("[OptionChain] ✗ Parsed 0 strikes — falling back")
#             return self._fallback(underlying, spot_price, 12, step)

#         print(f"[OptionChain] ✓ Parsed {len(strikes_data)} strikes from live data")

#         pcr        = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
#         max_pain   = self._max_pain(strikes_data)
#         vix        = self._get_vix()
#         ai_conf    = self._confidence(pcr, spot_price, atm_strike)

#         return {
#             "success":           True,
#             "live":              True,
#             "underlying":        config["display_name"],
#             "spot_price":        round(spot_price, 2),
#             "atm_strike":        atm_strike,
#             "pcr":               pcr,
#             "pcr_signal":        "BULLISH" if pcr > 1.2 else ("BEARISH" if pcr < 0.8 else "NEUTRAL"),
#             "max_pain":          max_pain,
#             "vix":               round(vix, 2),
#             "ai_confidence":     ai_conf,
#             "ai_confidence_label": "HIGH PROB" if ai_conf >= 70 else ("MEDIUM PROB" if ai_conf >= 50 else "LOW PROB"),
#             "strikes":           strikes_data
#         }

#     # ─────────────────────────────────────────────
#     # FALLBACK (synthetic but realistic)
#     # ─────────────────────────────────────────────
#     def _fallback(self, underlying, spot_price, num_strikes=12, step=50):
#         """Generate synthetic but realistic option chain as fallback."""
#         print(f"[OptionChain] ⚠ Generating synthetic fallback for {underlying}")
#         config     = self.INDEX_CONFIG.get(underlying, self.INDEX_CONFIG["NIFTY"])
#         step       = config["step"]
#         if spot_price == 0:
#             spot_price = config["default_spot"]

#         atm_strike   = round(spot_price / step) * step
#         strikes_data = []
#         total_ce_oi  = 0
#         total_pe_oi  = 0

#         for i in range(-num_strikes, num_strikes + 1):
#             strike = atm_strike + i * step
#             dist   = abs(i) / max(num_strikes, 1)

#             if strike <= atm_strike:
#                 ce_ltp   = max(0.05, (atm_strike - strike) / step * 12 + 5)
#                 ce_oi    = int(90000 - dist * 65000)
#                 ce_delta = round(min(0.95, 0.5 + (atm_strike - strike) / step * 0.22), 3)
#             else:
#                 ce_ltp   = max(0.05, 40 - (strike - atm_strike) / step * 4)
#                 ce_oi    = int(12000 + dist * 55000)
#                 ce_delta = round(max(0.05, 0.5 - (strike - atm_strike) / step * 0.22), 3)

#             if strike >= atm_strike:
#                 pe_ltp   = max(0.05, (strike - atm_strike) / step * 12 + 5)
#                 pe_oi    = int(90000 - dist * 65000)
#                 pe_delta = round(-min(0.95, 0.5 + (strike - atm_strike) / step * 0.22), 3)
#             else:
#                 pe_ltp   = max(0.05, 40 - (atm_strike - strike) / step * 4)
#                 pe_oi    = int(12000 + dist * 55000)
#                 pe_delta = round(-max(0.05, 0.5 - (atm_strike - strike) / step * 0.22), 3)

#             ce_oi = max(1000, ce_oi)
#             pe_oi = max(1000, pe_oi)
#             ce_oi_change = int((0.5 - dist) * 4500 * (1 if i < 0 else -1))
#             pe_oi_change = int((0.5 - dist) * 4500 * (1 if i > 0 else -1))
#             total_ce_oi += ce_oi
#             total_pe_oi += pe_oi

#             gamma = round(max(0.0001, 0.0035 - dist * 0.0003), 5)
#             theta = round(-12 - dist * 3, 2)
#             vega  = round(max(2, 12 - dist * 1.5), 2)

#             strikes_data.append({
#                 "strike": strike,
#                 "ce": {
#                     "ltp": round(ce_ltp, 2), "oi": ce_oi, "oi_change": ce_oi_change,
#                     "iv": 14.20, "delta": ce_delta, "theta": theta, "gamma": gamma,
#                     "vega": vega, "signal": self._signal(ce_oi_change)
#                 },
#                 "pe": {
#                     "ltp": round(pe_ltp, 2), "oi": pe_oi, "oi_change": pe_oi_change,
#                     "iv": 14.20, "delta": pe_delta, "theta": theta, "gamma": gamma,
#                     "vega": vega, "signal": self._signal(pe_oi_change)
#                 }
#             })

#         pcr      = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
#         max_pain = self._max_pain(strikes_data)
#         vix      = self._get_vix()
#         ai_conf  = self._confidence(pcr, spot_price, atm_strike)

#         return {
#             "success":           True,
#             "live":              False,   # ← flag so UI can show "SIMULATED"
#             "underlying":        config["display_name"],
#             "spot_price":        round(spot_price, 2),
#             "atm_strike":        atm_strike,
#             "pcr":               pcr,
#             "pcr_signal":        "BULLISH" if pcr > 1.2 else ("BEARISH" if pcr < 0.8 else "NEUTRAL"),
#             "max_pain":          max_pain,
#             "vix":               round(vix, 2),
#             "ai_confidence":     ai_conf,
#             "ai_confidence_label": "HIGH PROB" if ai_conf >= 70 else ("MEDIUM PROB" if ai_conf >= 50 else "LOW PROB"),
#             "strikes":           strikes_data
#         }

#     # ─────────────────────────────────────────────
#     # HELPERS
#     # ─────────────────────────────────────────────
#     def _signal(self, oi_change):
#         if oi_change > 1000:
#             return "▲ BULLISH"
#         if oi_change < -1000:
#             return "▼ BEARISH"
#         return "● NEUTRAL"

#     def _get_vix(self):
#         try:
#             d = self.tsl.get_ltp_data(names=["INDIA VIX"])
#             if d and "INDIA VIX" in d and float(d["INDIA VIX"]) > 0:
#                 return float(d["INDIA VIX"])
#         except Exception:
#             pass
#         return 14.20

#     def _max_pain(self, strikes_data):
#         """True max-pain: find the strike that causes maximum writer profit."""
#         try:
#             best_strike = None
#             best_pain   = float("inf")
#             for candidate in strikes_data:
#                 k  = candidate["strike"]
#                 tp = 0.0
#                 for s in strikes_data:
#                     sk = s["strike"]
#                     # CE writer gains when price < strike
#                     tp += max(0, sk - k) * s["ce"]["oi"]
#                     # PE writer gains when price > strike
#                     tp += max(0, k - sk) * s["pe"]["oi"]
#                 if tp < best_pain:
#                     best_pain   = tp
#                     best_strike = k
#             return best_strike or strikes_data[len(strikes_data) // 2]["strike"]
#         except Exception:
#             return strikes_data[len(strikes_data) // 2]["strike"] if strikes_data else 0

#     def _confidence(self, pcr, spot, atm):
#         conf = 50
#         if pcr > 1.2:   conf += 20
#         elif pcr > 1.0: conf += 10
#         elif pcr < 0.8: conf -= 15
#         elif pcr < 0.9: conf -= 5
#         if spot > atm:  conf += 10
#         elif spot < atm:conf -= 5
#         return min(95, max(30, conf))



###############################################################################################################################################################





# option_chain_service.py - PROPER DHAN API VERSION
import pandas as pd
import numpy as np
from datetime import datetime

class OptionChainService:
    def __init__(self, tsl):
        self.tsl = tsl
        self.debug = True

        self.INDEX_CONFIG = {
            "NIFTY": {
                "api_name": "NIFTY",
                "display_name": "NIFTY",
                "exchange": "INDEX",
                "step": 50,
                "default_spot": 20000
            },
            "BANKNIFTY": {
                "api_name": "BANKNIFTY",
                "display_name": "BANKNIFTY",
                "exchange": "INDEX",
                "step": 100,
                "default_spot": 20000
            },
            "FINNIFTY": {
                "api_name": "FINNIFTY",
                "display_name": "FINNIFTY",
                "exchange": "INDEX",
                "step": 50,
                "default_spot": 20000
            },
            "SENSEX": {
                "api_name": "SENSEX",
                "display_name": "SENSEX",
                "exchange": "INDEX",
                "step": 100,
                "default_spot": 20000
            }
        }




    def _format_live_chain(self, oc_df, underlying, spot_price, step):
        """Format live option chain data from Dhan API"""
        try:
            from config import Config
            
            atm_strike = round(spot_price / step) * step
            strikes_data = []
            total_ce_oi = 0
            total_pe_oi = 0
            
            # Normalize column names
            oc_df.columns = [str(c).strip() for c in oc_df.columns]
            
            for _, row in oc_df.iterrows():
                strike = self._safe_float(row.get('Strike Price', 0))
                if strike == 0:
                    continue
                
                # CE Data
                ce_ltp = self._safe_float(row.get('CE LTP', 0))
                ce_oi = self._safe_int(row.get('CE OI', 0))
                ce_oi_change = self._safe_int(row.get('CE Chg in OI', 0))
                ce_iv = self._safe_float(row.get('CE IV', 14.2))
                ce_delta = self._safe_float(row.get('CE Delta', 0))
                ce_theta = self._safe_float(row.get('CE Theta', 0))
                ce_gamma = self._safe_float(row.get('CE Gamma', 0))
                ce_vega = self._safe_float(row.get('CE Vega', 0))
                
                # PE Data
                pe_ltp = self._safe_float(row.get('PE LTP', 0))
                pe_oi = self._safe_int(row.get('PE OI', 0))
                pe_oi_change = self._safe_int(row.get('PE Chg in OI', 0))
                pe_iv = self._safe_float(row.get('PE IV', 14.2))
                pe_delta = self._safe_float(row.get('PE Delta', 0))
                pe_theta = self._safe_float(row.get('PE Theta', 0))
                pe_gamma = self._safe_float(row.get('PE Gamma', 0))
                pe_vega = self._safe_float(row.get('PE Vega', 0))
                
                total_ce_oi += ce_oi
                total_pe_oi += pe_oi
                
                # Signals
                ce_signal = '🟢 BULLISH' if ce_oi_change > 1000 else ('🔴 BEARISH' if ce_oi_change < -1000 else '⚪ NEUTRAL')
                pe_signal = '🟢 BULLISH' if pe_oi_change > 1000 else ('🔴 BEARISH' if pe_oi_change < -1000 else '⚪ NEUTRAL')
                
                strikes_data.append({
                    'strike': int(strike),
                    'ce': {
                        'ltp': round(ce_ltp, 2),
                        'oi': ce_oi,
                        'oi_change': ce_oi_change,
                        'iv': round(ce_iv, 2),
                        'delta': round(ce_delta, 3),
                        'theta': round(ce_theta, 2),
                        'gamma': round(ce_gamma, 5),
                        'vega': round(ce_vega, 2),
                        'signal': ce_signal
                    },
                    'pe': {
                        'ltp': round(pe_ltp, 2),
                        'oi': pe_oi,
                        'oi_change': pe_oi_change,
                        'iv': round(pe_iv, 2),
                        'delta': round(pe_delta, 3),
                        'theta': round(pe_theta, 2),
                        'gamma': round(pe_gamma, 5),
                        'vega': round(pe_vega, 2),
                        'signal': pe_signal
                    }
                })
            
            if not strikes_data:
                return None
            
            strikes_data.sort(key=lambda x: x['strike'])
            
            # Filter to strikes near ATM
            atm_idx = 0
            for i, s in enumerate(strikes_data):
                if s['strike'] >= atm_strike:
                    atm_idx = i
                    break
            
            num_strikes = 12
            start_idx = max(0, atm_idx - num_strikes)
            end_idx = min(len(strikes_data), atm_idx + num_strikes + 1)
            strikes_data = strikes_data[start_idx:end_idx]
            
            pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
            vix = self._get_vix()
            ai_conf = self._calculate_confidence(pcr, spot_price, atm_strike)
            
            return {
                'success': True,
                'live': True,
                'underlying': underlying,
                'spot_price': round(spot_price, 2),
                'atm_strike': atm_strike,
                'pcr': pcr,
                'pcr_signal': 'BULLISH' if pcr > 1.2 else ('BEARISH' if pcr < 0.8 else 'NEUTRAL'),
                'max_pain': atm_strike,
                'vix': round(vix, 2),
                'ai_confidence': ai_conf,
                'ai_confidence_label': 'HIGH' if ai_conf >= 70 else ('MEDIUM' if ai_conf >= 50 else 'LOW'),
                'strikes': strikes_data
            }
            
        except Exception as e:
            print(f"[Format] Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fallback(self, underlying, spot_price, num_strikes=12, step=50):
        """Generate synthetic option chain data as fallback"""
        try:
            from config import Config
            
            configs = {
                "NIFTY": {"step": 50, "default_spot": 20000},
                "BANKNIFTY": {"step": 100, "default_spot": 20000},
                "FINNIFTY": {"step": 50, "default_spot": 20000},
                "SENSEX": {"step": 100, "default_spot": 20000}
            }
            
            cfg = configs.get(underlying, configs["NIFTY"])
            step = cfg["step"]
            
            if spot_price == 0:
                spot_price = cfg["default_spot"]
            
            atm_strike = round(spot_price / step) * step
            strikes_data = []
            total_ce_oi = 0
            total_pe_oi = 0
            
            for i in range(-num_strikes, num_strikes + 1):
                strike = atm_strike + (i * step)
                distance = abs(i) / num_strikes
                
                # CE Premium
                if strike <= spot_price:
                    ce_ltp = max(0.5, round((spot_price - strike) / step * 10 + 5, 2))
                    ce_delta = round(0.5 + (spot_price - strike) / step * 0.25, 3)
                    ce_oi = int(40000 - distance * 35000)
                else:
                    ce_ltp = max(0.5, round(35 - (strike - spot_price) / step * 5, 2))
                    ce_delta = round(0.5 - (strike - spot_price) / step * 0.25, 3)
                    ce_oi = int(8000 + distance * 20000)
                
                # PE Premium
                if strike >= spot_price:
                    pe_ltp = max(0.5, round((strike - spot_price) / step * 10 + 5, 2))
                    pe_delta = round(-0.5 - (strike - spot_price) / step * 0.25, 3)
                    pe_oi = int(40000 - distance * 35000)
                else:
                    pe_ltp = max(0.5, round(35 - (spot_price - strike) / step * 5, 2))
                    pe_delta = round(-0.5 + (spot_price - strike) / step * 0.25, 3)
                    pe_oi = int(8000 + distance * 20000)
                
                ce_oi = max(1000, ce_oi)
                pe_oi = max(1000, pe_oi)
                
                ce_oi_change = int(800 * (1 - distance) * (1 if i < 0 else -1))
                pe_oi_change = int(800 * (1 - distance) * (1 if i > 0 else -1))
                
                total_ce_oi += ce_oi
                total_pe_oi += pe_oi
                
                ce_signal = '🟢 BULLISH' if ce_oi_change > 500 else ('🔴 BEARISH' if ce_oi_change < -500 else '⚪ NEUTRAL')
                pe_signal = '🟢 BULLISH' if pe_oi_change > 500 else ('🔴 BEARISH' if pe_oi_change < -500 else '⚪ NEUTRAL')
                
                strikes_data.append({
                    'strike': strike,
                    'ce': {
                        'ltp': ce_ltp,
                        'oi': ce_oi,
                        'oi_change': ce_oi_change,
                        'iv': 14.2,
                        'delta': ce_delta,
                        'theta': -10,
                        'gamma': 0.003,
                        'vega': 10,
                        'signal': ce_signal
                    },
                    'pe': {
                        'ltp': pe_ltp,
                        'oi': pe_oi,
                        'oi_change': pe_oi_change,
                        'iv': 14.2,
                        'delta': pe_delta,
                        'theta': -10,
                        'gamma': 0.003,
                        'vega': 10,
                        'signal': pe_signal
                    }
                })
            
            # Calculate PCR
            if total_ce_oi > 0:
                pcr = round(total_pe_oi / total_ce_oi, 2)
            else:
                pcr = 1.0
            
            vix = self._get_vix()
            
            return {
                'success': True,
                'live': False,
                'underlying': underlying,
                'spot_price': round(spot_price, 2),
                'atm_strike': atm_strike,
                'pcr': pcr,
                'pcr_signal': 'BULLISH' if pcr > 1.2 else ('BEARISH' if pcr < 0.8 else 'NEUTRAL'),
                'max_pain': atm_strike,
                'vix': round(vix, 2),
                'ai_confidence': 50,
                'ai_confidence_label': 'MEDIUM',
                'strikes': strikes_data
            }
            
        except Exception as e:
            print(f"[Fallback] Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_vix(self):
        """Get India VIX value"""
        try:
            vix_data = self.tsl.get_ltp_data(names=["INDIA VIX"])
            if vix_data and "INDIA VIX" in vix_data:
                return float(vix_data["INDIA VIX"])
        except:
            pass
        return 14.2
    
    def _calculate_confidence(self, pcr, spot, atm):
        """Calculate confidence score"""
        conf = 50
        if pcr > 1.2:
            conf += 20
        elif pcr > 1.0:
            conf += 10
        elif pcr < 0.8:
            conf -= 15
        if spot > atm:
            conf += 10
        elif spot < atm:
            conf -= 5
        return min(95, max(30, conf))
    
    def _safe_float(self, value, default=0.0):
        """Safely convert to float"""
        try:
            if value is None or value == '':
                return default
            return float(value)
        except:
            return default
    
    def _safe_int(self, value, default=0):
        """Safely convert to int"""
        try:
            if value is None or value == '':
                return default
            return int(float(value))
        except:
            return default





    def _get_spot_price_from_historical(self, symbol):
        """Get spot price from historical data (works even after market hours)"""
        try:
            from datetime import datetime, timedelta
            
            # Map to correct API symbol names
            symbol_map = {
                "NIFTY": "NIFTY",
                "BANKNIFTY": "BANKNIFTY",
                "FINNIFTY": "FINNIFTY",
                "SENSEX": "SENSEX"
            }
            
            api_symbol = symbol_map.get(symbol, symbol)
            
            # Get last 5 days of daily data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            # Determine exchange
            exchange = "INDEX"
            
            hist_data = self.tsl.get_long_term_historical_data(
                tradingsymbol=api_symbol,
                exchange=exchange,
                timeframe='DAY',
                from_date=start_date,
                to_date=end_date
            )
            
            if hist_data is not None and not hist_data.empty:
                last_close = float(hist_data['close'].iloc[-1])
                print(f"[SpotPrice] Historical close for {api_symbol}: {last_close}")
                return last_close
            else:
                print(f"[SpotPrice] No historical data for {api_symbol}")
                
        except Exception as e:
            print(f"[SpotPrice] Historical data error: {e}")
        
        # Fallback to defaults
        defaults = {
            "NIFTY": 20000,
            "BANKNIFTY": 20000,
            "FINNIFTY": 20000,
            "SENSEX": 20000
        }
        return defaults.get(symbol, 20000)




    def get_option_chain(self, underlying:str, expiry_index:int=0, num_strikes:int=20):
        """
        Get option chain using Dhan_Tradehull get_option_chain method
        Falls back to synthetic data when API fails
        """
        try:
            config = self.INDEX_CONFIG.get(underlying, self.INDEX_CONFIG["NIFTY"])
            api_name = config["api_name"]
            exchange = config["exchange"]
            step = config["step"]
            
            print(f"\n[OptionChain] Fetching: {underlying} (api_name={api_name}, exchange={exchange}, expiry_index={expiry_index})")
            
            # Get spot price
            spot_price = self._get_spot_price(api_name)
            if spot_price == 0 or spot_price < 10000:
                spot_price = self._get_spot_price_from_historical(api_name)
                print(f"[OptionChain] Using default spot: {spot_price}")
            
            # Try to get real option chain
            try:
                result = self.tsl.get_option_chain(
                    Underlying=api_name,
                    exchange=exchange,
                    expiry=expiry_index,
                    num_strikes=num_strikes * 2
                )
                
                if result is not None and isinstance(result, tuple) and len(result) == 2:
                    atm_strike = result[0]
                    oc_df = result[1]
                    
                    if oc_df is not None and not oc_df.empty:
                        print(f"[OptionChain] ✅ Got REAL data! ATM: {atm_strike}, shape: {oc_df.shape}")
                        formatted = self._format_live_chain(oc_df, underlying, spot_price, step)
                        if formatted:
                            return formatted
                        else:
                            print(f"[OptionChain] Formatting failed, using fallback")
                    else:
                        print(f"[OptionChain] DataFrame is empty, using fallback")
                else:
                    print(f"[OptionChain] Invalid result format, using fallback")
                    
            except Exception as e:
                print(f"[OptionChain] Real API failed: {e}")
            
            # FALLBACK to synthetic data
            print(f"[OptionChain] ⚠️ Using SYNTHETIC fallback data for {underlying}")
            return self._fallback(underlying, spot_price, num_strikes, step)
            
        except Exception as e:
            print(f"[OptionChain] Error: {e}")
            import traceback
            traceback.print_exc()
            # Final fallback
            config = self.INDEX_CONFIG.get(underlying, self.INDEX_CONFIG["NIFTY"])
            spot_price = config["default_spot"]
            step = config["step"]
            return self._fallback(underlying, spot_price, num_strikes, step)
    

    def _get_spot_price(self, symbol):
        """Get spot price using get_ltp_data"""
        try:
            # Map to correct API symbol names
            symbol_map = {
                "NIFTY": "NIFTY",
                "BANKNIFTY": "BANKNIFTY",
                "FINNIFTY": "FINNIFTY",
                "SENSEX": "SENSEX"
            }
            
            api_symbol = symbol_map.get(symbol, symbol)
            
            ltp_data = self.tsl.get_ltp_data(names=[api_symbol])
            if ltp_data and api_symbol in ltp_data:
                val = ltp_data[api_symbol]
                if val and float(val) > 0:
                    print(f"[SpotPrice] Live LTP for {api_symbol}: {val}")
                    return float(val)
                    
        except Exception as e:
            print(f"[SpotPrice] Live LTP error: {e}")
        
        return 0  # Return 0 to trigger historical fallback


    def _format_dhan_data(self, df, underlying, spot_price, atm_strike, num_strikes):
        """Format Dhan's option chain DataFrame to our JSON format"""
        try:
            strikes_data = []
            total_ce_oi = 0
            total_pe_oi = 0
            
            # Dhan's DataFrame columns
            # CE columns: 'CE OI', 'CE Chg in OI', 'CE Volume', 'CE IV', 'CE LTP', 'CE Bid', 'CE Ask', etc.
            # PE columns: 'PE OI', 'PE Chg in OI', 'PE Volume', 'PE IV', 'PE LTP', etc.
            
            for _, row in df.iterrows():
                strike = row.get('Strike Price', 0)
                if not strike:
                    continue
                
                # CE Data - use actual column names from Dhan
                ce_ltp = float(row.get('CE LTP', 0)) if pd.notna(row.get('CE LTP')) else 0
                ce_oi = int(row.get('CE OI', 0)) if pd.notna(row.get('CE OI')) else 0
                ce_oi_change = int(row.get('CE Chg in OI', 0)) if pd.notna(row.get('CE Chg in OI')) else 0
                ce_iv = float(row.get('CE IV', 0)) if pd.notna(row.get('CE IV')) else 0
                ce_delta = float(row.get('CE Delta', 0)) if pd.notna(row.get('CE Delta')) else 0
                ce_theta = float(row.get('CE Theta', 0)) if pd.notna(row.get('CE Theta')) else 0
                ce_gamma = float(row.get('CE Gamma', 0)) if pd.notna(row.get('CE Gamma')) else 0
                ce_vega = float(row.get('CE Vega', 0)) if pd.notna(row.get('CE Vega')) else 0
                
                # PE Data
                pe_ltp = float(row.get('PE LTP', 0)) if pd.notna(row.get('PE LTP')) else 0
                pe_oi = int(row.get('PE OI', 0)) if pd.notna(row.get('PE OI')) else 0
                pe_oi_change = int(row.get('PE Chg in OI', 0)) if pd.notna(row.get('PE Chg in OI')) else 0
                pe_iv = float(row.get('PE IV', 0)) if pd.notna(row.get('PE IV')) else 0
                pe_delta = float(row.get('PE Delta', 0)) if pd.notna(row.get('PE Delta')) else 0
                pe_theta = float(row.get('PE Theta', 0)) if pd.notna(row.get('PE Theta')) else 0
                pe_gamma = float(row.get('PE Gamma', 0)) if pd.notna(row.get('PE Gamma')) else 0
                pe_vega = float(row.get('PE Vega', 0)) if pd.notna(row.get('PE Vega')) else 0
                
                total_ce_oi += ce_oi
                total_pe_oi += pe_oi
                
                # Signals based on OI change
                if ce_oi_change > 1000:
                    ce_signal = '🟢 BULLISH'
                elif ce_oi_change < -1000:
                    ce_signal = '🔴 BEARISH'
                else:
                    ce_signal = '⚪ NEUTRAL'
                
                if pe_oi_change > 1000:
                    pe_signal = '🟢 BULLISH'
                elif pe_oi_change < -1000:
                    pe_signal = '🔴 BEARISH'
                else:
                    pe_signal = '⚪ NEUTRAL'
                
                strikes_data.append({
                    'strike': int(strike),
                    'ce': {
                        'ltp': round(ce_ltp, 2) if ce_ltp > 0 else 0,
                        'oi': ce_oi,
                        'oi_change': ce_oi_change,
                        'iv': round(ce_iv, 2) if ce_iv > 0 else 0,
                        'delta': round(ce_delta, 4) if ce_delta != 0 else 0,
                        'theta': round(ce_theta, 2) if ce_theta != 0 else 0,
                        'gamma': round(ce_gamma, 5) if ce_gamma != 0 else 0,
                        'vega': round(ce_vega, 2) if ce_vega != 0 else 0,
                        'signal': ce_signal
                    },
                    'pe': {
                        'ltp': round(pe_ltp, 2) if pe_ltp > 0 else 0,
                        'oi': pe_oi,
                        'oi_change': pe_oi_change,
                        'iv': round(pe_iv, 2) if pe_iv > 0 else 0,
                        'delta': round(pe_delta, 4) if pe_delta != 0 else 0,
                        'theta': round(pe_theta, 2) if pe_theta != 0 else 0,
                        'gamma': round(pe_gamma, 5) if pe_gamma != 0 else 0,
                        'vega': round(pe_vega, 2) if pe_vega != 0 else 0,
                        'signal': pe_signal
                    }
                })
            
            # Sort strikes
            strikes_data.sort(key=lambda x: x['strike'])
            
            # Filter to strikes near ATM
            atm_idx = 0
            for i, s in enumerate(strikes_data):
                if s['strike'] >= atm_strike:
                    atm_idx = i
                    break
            
            start_idx = max(0, atm_idx - num_strikes)
            end_idx = min(len(strikes_data), atm_idx + num_strikes + 1)
            strikes_data = strikes_data[start_idx:end_idx]
            
            # Calculate PCR
            pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
            
            # Get VIX
            vix = self._get_vix()
            
            # AI Confidence
            ai_conf = self._calculate_confidence(pcr, spot_price, atm_strike)
            
            print(f"[OptionChain] Formatted {len(strikes_data)} strikes (ATM: {atm_strike}, PCR: {pcr})")
            
            return {
                'success': True,
                'live': True,
                'underlying': underlying,
                'spot_price': round(spot_price, 2),
                'atm_strike': atm_strike,
                'pcr': pcr,
                'pcr_signal': 'BULLISH' if pcr > 1.2 else ('BEARISH' if pcr < 0.8 else 'NEUTRAL'),
                'max_pain': atm_strike,
                'vix': round(vix, 2),
                'ai_confidence': ai_conf,
                'ai_confidence_label': 'HIGH' if ai_conf >= 70 else ('MEDIUM' if ai_conf >= 50 else 'LOW'),
                'strikes': strikes_data
            }
            
        except Exception as e:
            print(f"[Format] Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_vix(self):
        try:
            vix_data = self.tsl.get_ltp_data(names=["INDIA VIX"])
            if vix_data and "INDIA VIX" in vix_data:
                return float(vix_data["INDIA VIX"])
        except:
            pass
        return 14.2

    def _calculate_confidence(self, pcr, spot, atm):
        conf = 50
        if pcr > 1.2:
            conf += 20
        elif pcr > 1.0:
            conf += 10
        elif pcr < 0.8:
            conf -= 15
        if spot > atm:
            conf += 10
        elif spot < atm:
            conf -= 5
        return min(95, max(30, conf))
