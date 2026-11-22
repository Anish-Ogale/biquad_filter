# PROPOSAL_SYNC — specification changes to copy into the proposal

Date: 2026-11-22. This file is for synchronizing the proposal document and is
**not** part of the final source ZIP.

## Changed specification rows

| Item | Old value | New value | Reason / measured evidence |
|---|---|---|---|
| f0 accuracy, typ | ±1 % for all K | **±1 % for K≤100, ±1.5 % for K=200** | Quantization is +1.24 % at K=200/Q=5 and ≤0.93 % for K≤100 [ANALYTICAL]. Max remains ±3 %. |
| Gain implementation | Input capacitive attenuator | **Input-branch cap Cs1 = G*Cs** (G = 1, 2, 3.98, 7.94) | An attenuator cannot provide +6/+12/+18 dB. Simulated LP gain error is ≤0.060 dB. Cs2/Cs3/Cd/CI unchanged, so f0/Q do not move. |
| Input range | Input range ±1 V differential | **Output swing ±1 V differential**; usable input = ±1 V / G; BP peak gain = G*Q | Gain is now >1, so input range scales with gain. |
| THD condition | 1 Vpp differential at f (ambiguously input) | **1 Vpp differential at the LP output, f = f0/4** | THD is an output-referred specification. |
| Output offset, 0 dB/Q≤2/all K | typ ±10 mV, max ±30 mV | **max ±40 mV, no typ value**, for assumed 5 mV op-amp input offset | 80-run matrix gives 29.4 mV worst at 60 dB baseline; real tt/ss worst cases 35.3/34.0 mV; ideal 80 dB worst 36.5 mV at 0 dB. |
| Output offset, all gain/Q | typ ±20 mV, max ±60 mV | **max ±60 mV, no typ value**, for assumed 5 mV op-amp input offset | 45.5 mV worst at 60 dB baseline; real tt/ss 35.3/34.0 mV; ideal 80 dB 53.5 mV. Measured offset gain ≈5.9x (0 dB/Q≤2) and 9.1x (all settings). |
| IDDA at fclk = 1 MHz | typ 0.8 mA, max 1.5 mA | **typ 1.3 mA, max 2.0 mA** | Measured 1.22 mA typ at tt, 1.02 mA ss, 1.43 mA ff (2×op-amp + 60 µA replica) [SIM]. The max is stated excluding output buffers, bias, CMFB and clock generation. |
| Cap budget | 60–100 pF target; old table 32.6–54.6 pF | **≤120 pF target; 33.6–68.7 pF at 0 dB, 37.2–117.6 pF at 18 dB** | Gain branch Cs1=G*Cs and full counting of both halves/all branches (2×Cs1 + 4×Cs + 2×Cd + 4×CI) [ANALYTICAL]. |
| Area | MiM caps reported as 0.0351 mm² | **MiM area 0.0585 mm² maximum at 18 dB**; spec remains 0.12 mm² | Full topology and 18 dB input branch. Report is **MiM capacitance only**; switches, op-amps, bias and routing are not included. |
| Output noise | 70–80 µVrms [EST] | **66.7 µVrms at 0 dB, 87.2 µVrms at 18 dB worst [EST]** | Re-computed sampled kT/C over both halves of Cs1/Cs2/Cs3/Cd/CI, power-summed; excludes 1/f, op-amp, THD and clock-feedthrough noise. Spec typ/max stay 150/400 µVrms. |

## Unchanged specs with new evidence / limitations

| Item | Spec | Status |
|---|---|---|
| Gain error | ±0.5 dB typ / ±1 dB max | PASS: worst 0.060 dB over ideal/tt/ss. |
| Q accuracy | ±5 % typ; ±15 % max (Q≤2), ±20 % max (Q>2) | K=200/Q=5 gives Q −14.8 % (0 dB) and −15.1 % (18 dB) even at ideal 80 dB/10 MHz: inside max ±20 %, outside the ±5 % sweep criterion. Q≤2 at 18 dB is 5.0–6.3 % at the current 49–50 dB corners but 1.9 % worst at A0=60 dB (`results/q2check.md`), so the 60 dB A0 requirement covers it. |
| Clock feedthrough | 5/20 mVpp | NOT YET MEASURED; planned post-acceptance. |
| THD / noise simulation | −60/−50 dB; 150/400 µVrms | THD and transient noise simulation planned; only the kT/C noise estimate exists now [EST]. |
| IDDD | 40/100 µA | PLANNED; no digital logic in prototype. |
| Op-amp A0/GBW | A0 ≥50 dB min (80 dB goal), GBW ≥10 MHz, PM ≥45° | tt/ff meet 50 dB and 10 MHz; ss is 49.0 dB/7.82 MHz and misses both. All three are below the 60 dB A0 needed at 18 dB gain. 80 dB goal not met. No relaxed spec. |

## Planned offset re-derivation

1. Estimate the real 5 V input-pair offset with a manual Pelgrom model
   (stock PDK mismatch is disabled) [EST].
2. Re-derive the ±40/±60 mV output-offset limits from that op-amp offset and
   the measured ≈5.9x/9.1x offset gains.
3. Re-run the same-sign/opposite-sign matrix at the resulting op-amp offset.
