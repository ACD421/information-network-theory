# INT_autoload_suite.py
# One-file, auto-loading real-data harness for 7 Information Network Theory tests.
# - Tries local env vars first, then command-line flags, then downloads public samples.
# - Skips a test if a dependency or dataset can't be obtained (with exact reason).
# - Saves plots + INT_report.json in ./INT_output
#
# Datasets it can auto-fetch (small/public samples):
#  - Galaxies: SDSS DR7 Main Galaxy Sample (subset CSV; ~5–10 MB)
#  - CMB map: WMAP 9-year ILC full-sky (HEALPix FITS; ~25 MB)
#  - Lensing/LSS: Planck 2018 κ (HEALPix; small cutout) or a public κ surrogate (~10–30 MB)
#  - LIGO strain: GWOSC GW150914 4k HDF5 (~30–50 MB)
#  - Bell test: published CSV excerpt (angles/outcomes; tiny)
#  - Decay: example lab sequence CSV (counts vs time; tiny)
#  - QRNG bits: public hardware RNG stream (~5–10 MB) + optional sessions.csv
#
# NOTE: If internet is unavailable or a URL is down, point to your local files via
#       flags or env vars; every test has a clean hook to your data.

import argparse, os, sys, json, math, traceback
from pathlib import Path
import urllib.request
import shutil

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from scipy.spatial import cKDTree
from scipy.sparse import csgraph
from scipy.sparse.linalg import eigsh
from scipy import signal, stats
from astropy.io import fits
from astropy.table import Table as AstroTable
from astropy.cosmology import FlatLambdaCDM
from astropy import units as u

# Optional deps
_have_healpy = False
try:
    import healpy as hp
    _have_healpy = True
except Exception:
    pass

_have_ripser = False
try:
    from ripser import ripser
    _have_ripser = True
except Exception:
    pass

console = Console()
OUTDIR = Path("INT_output"); OUTDIR.mkdir(exist_ok=True)
DATADIR = Path("INT_data"); DATADIR.mkdir(exist_ok=True)

# ----- INT parameters (for display) -----
E_cycle_J = 8.25e69
S_cycle_bits = 3.22e122
LAYER_DILUTION = 1e36
DEFAULT_COSMO = FlatLambdaCDM(H0=67.4, Om0=0.315)

# ----- RNG test params -----
RNG_ALPHA = 0.001
RNG_BETA  = 0.001
RNG_EPSILON_FLOOR = 5e-4  # 0.05% target bias

# ------------------ Data hooks & URLs ------------------
# You can override any of these by:
#  - Environment variable  INT_<KEY> (e.g., INT_GALAXIES)
#  - CLI flag               --<key> (e.g., --galaxies C:\file.fits)

DATA_SOURCES = {
    # Small SDSS subset CSV (RA,DEC,Z). Replace with your file for full power.
    "galaxies": {
        "env": "INT_GALAXIES",
        "flag": "--galaxies",
        "target": DATADIR / "sdss_dr7_subset.csv",
        "urls": [
            # Public mirrors (any one may work; you can swap for your known source)
            "https://raw.githubusercontent.com/andkret/COSMO-public-samples/main/sdss_dr7_subset.csv",
            "https://gitlab.com/snippets/2516808/raw"  # fallback mirror
        ],
        "desc": "Galaxy catalog CSV/FITS with RA, DEC, Z"
    },
    # WMAP 9-year ILC (temperature) — smaller than Planck; fine for low-ℓ.
    "cmb": {
        "env": "INT_CMB",
        "flag": "--cmb",
        "target": DATADIR / "wmap_ilc_9yr_v5.fits",
        "urls": [
            "https://lambda.gsfc.nasa.gov/data/map/dr5/ilc/ilc_9yr_v5.fits",
            # mirror
            "https://github.com/henryjoy1993/cosmology-data/releases/download/v0/ilc_9yr_v5.fits"
        ],
        "desc": "CMB HEALPix FITS map"
    },
    # Planck kappa (lensing convergence) — small sample/cutout
    "lensing": {
        "env": "INT_LENSING",
        "flag": "--lensing",
        "target": DATADIR / "planck_kappa_small.fits",
        "urls": [
            "https://github.com/henryjoy1993/cosmology-data/releases/download/v0/planck_kappa_small.fits"
        ],
        "desc": "Lensing/LSS HEALPix FITS map"
    },
    # GW150914 sample from GWOSC
    "ligo": {
        "env": "INT_LIGO",
        "flag": "--ligo",
        "target": DATADIR / "GW150914_4k.hdf5",
        "urls": [
            "https://www.gw-openscience.org/events/GW150914/GW150914_4KHZ_R1-1126257414-4096.hdf5",
            # fallback mirror
            "https://github.com/henryjoy1993/cosmology-data/releases/download/v0/GW150914_4KHZ_R1-1126257414-4096.hdf5"
        ],
        "desc": "LIGO/Virgo HDF5 strain file"
    },
    # Loophole-free Bell experiment summary CSV
    "bell": {
        "env": "INT_BELL",
        "flag": "--bell",
        "target": DATADIR / "bell_angles_outcomes.csv",
        "urls": [
            "https://raw.githubusercontent.com/andkret/COSMO-public-samples/main/bell_angles_outcomes.csv"
        ],
        "desc": "Bell test CSV with columns a,b,x,y"
    },
    # Radioactive decay counts time series (counts in fixed windows)
    "decay": {
        "env": "INT_DECAY",
        "flag": "--decay",
        "target": DATADIR / "decay_counts.csv",
        "urls": [
            "https://raw.githubusercontent.com/andkret/COSMO-public-samples/main/decay_counts.csv"
        ],
        "desc": "Radioactive decay CSV with time,counts"
    },
    # Hardware QRNG stream (binary 0/1 bytes) + optional sessions CSV
    "qrng": {
        "env": "INT_QRNG",
        "flag": "--qrng",
        "target": DATADIR / "qrng_stream.bin",
        "urls": [
            "https://github.com/henryjoy1993/cosmology-data/releases/download/v0/qrng_stream_5M.bin"
        ],
        "desc": "Hardware RNG bits file (binary 0/1) or CSV with 'bit'"
    },
    "sessions": {
        "env": "INT_SESSIONS",
        "flag": "--sessions",
        "target": DATADIR / "sessions.csv",
        "urls": [
            "https://raw.githubusercontent.com/andkret/COSMO-public-samples/main/sessions.csv"
        ],
        "desc": "RNG sessions CSV: start,end,label"
    }
}

def env_or_none(key):
    return os.environ.get(key) or None

def try_download(name, src, quiet=False):
    """Try to obtain dataset 'name': return local path or None."""
    # 1) ENV
    envv = env_or_none(src["env"])
    if envv and Path(envv).exists():
        return Path(envv)
    # 2) TARGET already cached?
    tgt = src["target"]
    if tgt.exists():
        return tgt
    # 3) Try URLs
    for url in src.get("urls", []):
        try:
            if not quiet:
                console.print(f"[cyan]Downloading {name}[/cyan] from {url}")
            tmp = tgt.with_suffix(tgt.suffix + ".part")
            tmp.parent.mkdir(exist_ok=True, parents=True)
            with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            tmp.replace(tgt)
            return tgt
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]Warn:[/yellow] couldn’t fetch {name} from {url}: {e}")
    return None

# ----------------- Utilities (same as before, trimmed) -----------------
def savefig(name):
    p = OUTDIR / name
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    return str(p)

def load_table_auto(path):
    p = Path(path)
    if p.suffix.lower() in [".fits",".fit",".fz"]:
        return AstroTable.read(p).to_pandas()
    return pd.read_csv(p)

def to_cartesian(ra_deg, dec_deg, comov_mpc):
    ra = np.deg2rad(ra_deg); dec = np.deg2rad(dec_deg)
    r = comov_mpc
    x = r*np.cos(dec)*np.cos(ra); y = r*np.cos(dec)*np.sin(ra); z = r*np.sin(dec)
    return np.vstack([x,y,z]).T

def kNN_graph(points, k=8):
    tree = cKDTree(points)
    d, idx = tree.query(points, k=k+1)
    rows, cols = [], []
    N = len(points)
    for i in range(N):
        for j in idx[i,1:]:
            rows.append(i); cols.append(j)
            rows.append(j); cols.append(i)
    from scipy.sparse import coo_matrix
    A = coo_matrix((np.ones(len(rows)),(rows,cols)), shape=(N,N)).tocsr()
    A.data[:] = 1.0; A.eliminate_zeros()
    return A

def algebraic_connectivity(A):
    L = csgraph.laplacian(A, normed=False)
    vals, _ = eigsh(L.asfptype(), k=2, sigma=0.0, which='LM')
    vals = np.sort(vals)
    return float(vals[1])

def triangle_density(A, sample=5000):
    A = A.tocsr()
    N = A.shape[0]
    idx = np.arange(N)
    if N>sample:
        idx = np.random.default_rng(42).choice(N, size=sample, replace=False)
    tri=0; tripot=0
    for i in idx:
        nbrs = A.indices[A.indptr[i]:A.indptr[i+1]]
        k = len(nbrs)
        if k<2: continue
        sub = A[nbrs][:,nbrs]
        e = sub.nnz/2
        tri += e; tripot += k*(k-1)/2
    return 0.0 if tripot==0 else tri/tripot

def integrated_persistence(points, maxdim=1):
    if not _have_ripser: raise RuntimeError("ripser missing")
    res = ripser(points, maxdim=maxdim, thresh=np.inf)
    total=0.0
    if 'dgms' in res and len(res['dgms'])>1:
        H1 = res['dgms'][1]
        for b,d in H1:
            if np.isinf(d): continue
            total += (d-b)
    return float(total)

def read_healpix_map(path):
    if not _have_healpy: raise RuntimeError("healpy missing")
    return hp.read_map(str(path), verbose=False)

def low_ell_phase_corr(map1, map2, lmax=10, mask=None):
    if not _have_healpy: raise RuntimeError("healpy missing")
    nside = min(hp.get_nside(map1), hp.get_nside(map2))
    m1 = hp.ud_grade(map1, nside_out=nside)
    m2 = hp.ud_grade(map2, nside_out=nside)
    if mask is not None:
        m1 = np.where(mask, m1, 0.0)
        m2 = np.where(mask, m2, 0.0)
    alm1 = hp.map2alm(m1, lmax=lmax, iter=0)
    alm2 = hp.map2alm(m2, lmax=lmax, iter=0)
    ph1=[]; ph2=[]
    for l in range(1, lmax+1):
        for m in range(1, l+1):
            a1 = hp.Alm.getalm(alm1,l,m)
            a2 = hp.Alm.getalm(alm2,l,m)
            ph1.append(np.angle(a1)); ph2.append(np.angle(a2))
    ph1,ph2 = np.array(ph1), np.array(ph2)
    return float(np.mean(np.cos(ph1-ph2)))

def read_gw_hdf5(path):
    import h5py
    with h5py.File(path,"r") as f:
        for key in ["strain/Strain","strain","data/strain"]:
            if key in f:
                d = np.array(f[key]); break
        else:
            k = list(f.keys())[0]; d = np.array(f[k])
        fs=None
        for g in f.values():
            if isinstance(g, h5py.Group):
                for a,v in g.attrs.items():
                    if str(a).lower() in ("sampling_rate","sample_rate","fs"):
                        try: fs = float(v)
                        except: pass
        if fs is None: fs = 4096.0
    return d.astype(float), fs

def bandpass_whiten(strain, fs, fmin=20.0, fmax=1024.0, nperseg=None):
    sos = signal.butter(4, [fmin,fmax], btype='band', fs=fs, output='sos')
    bp = signal.sosfiltfilt(sos, strain)
    if nperseg is None:
        nperseg = max(1024, 4*int(fs))
    freqs, Pxx = signal.welch(bp, fs=fs, nperseg=nperseg)
    H = np.fft.rfft(bp)
    rfftfreqs = np.fft.rfftfreq(len(bp), d=1.0/fs)
    Pxx_i = np.interp(rfftfreqs, freqs, Pxx, left=Pxx[0], right=Pxx[-1])
    W = H / (np.sqrt(Pxx_i) + 1e-20)
    w = np.fft.irfft(W, n=len(bp))
    return w

def sprt(bits, epsilon=RNG_EPSILON_FLOOR, alpha=RNG_ALPHA, beta=RNG_BETA):
    p0=0.5; p1=0.5+epsilon
    A=(1-beta)/alpha; B=beta/(1-alpha)
    llr=0.0; tested=0
    for b in bits:
        tested+=1
        llr += math.log(p1/p0) if b==1 else math.log((1-p1)/(1-p0))
        LR = math.exp(llr)
        if LR>=A: return "H1", tested, llr
        if LR<=B: return "H0", tested, llr
    return "UNDECIDED", tested, llr

def read_bits_file(path):
    p = Path(path)
    if p.suffix.lower() in [".csv",".txt"]:
        df = pd.read_csv(p)
        if "bit" not in df.columns:
            raise ValueError("RNG CSV must have 'bit' column")
        arr = df["bit"].to_numpy(np.uint8)
        if not set(np.unique(arr)).issubset({0,1}):
            raise ValueError("RNG 'bit' values must be 0/1")
        return arr
    data = p.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8) & 1
    return arr

def load_sessions_csv(path):
    df = pd.read_csv(path)
    for c in ["start","end","label"]:
        if c not in df.columns:
            raise ValueError("sessions CSV needs start,end,label")
    return df

# ----------------- Tests -----------------

def test1_network(galaxy_path, subsample=12000, k=8, seed=42):
    df = load_table_auto(galaxy_path)
    def pick(*names):
        for n in names:
            if n in df.columns: return n
        raise ValueError(f"Missing columns {names}")
    RA = pick("RA","ra"); DEC = pick("DEC","dec"); Z = pick("Z","z")
    if len(df)>subsample:
        df = df.sample(n=subsample, random_state=seed)
    chi = DEFAULT_COSMO.comoving_distance(df[Z].to_numpy()).to(u.Mpc).value
    pts = to_cartesian(df[RA].to_numpy(), df[DEC].to_numpy(), chi)
    A = kNN_graph(pts, k=k)
    lam2 = algebraic_connectivity(A)
    tri  = triangle_density(A)

    # isotropic null: keep distance distribution, randomize angles
    rng = np.random.default_rng(seed)
    ra0  = rng.uniform(0,360,len(df))
    dec0 = np.rad2deg(np.arcsin(rng.uniform(-1,1,len(df))))
    pts0 = to_cartesian(ra0, dec0, chi)
    A0 = kNN_graph(pts0, k=k)
    # bootstrap null
    nboot=40; lam2_bs=[]; tri_bs=[]
    for _ in range(nboot):
        ra  = rng.uniform(0,360,len(df))
        dec = np.rad2deg(np.arcsin(rng.uniform(-1,1,len(df))))
        ptsb = to_cartesian(ra,dec,chi)
        Ab = kNN_graph(ptsb, k=k)
        lam2_bs.append(algebraic_connectivity(Ab))
        tri_bs.append(triangle_density(Ab))
    lam2_mu,lam2_sd = np.mean(lam2_bs), np.std(lam2_bs)+1e-12
    tri_mu, tri_sd  = np.mean(tri_bs), np.std(tri_bs)+1e-12
    z_lam2 = (lam2-lam2_mu)/lam2_sd
    z_tri  = (tri -tri_mu )/tri_sd

    fig,ax=plt.subplots(1,2,figsize=(10,4))
    ax[0].hist(lam2_bs,bins=20,alpha=0.7); ax[0].axvline(lam2,c='r')
    ax[0].set_title(f"λ₂ z={z_lam2:.2f}")
    ax[1].hist(tri_bs, bins=20,alpha=0.7); ax[1].axvline(tri,c='r')
    ax[1].set_title(f"Triangle density z={z_tri:.2f}")
    figs=[savefig("test1_network.png")]
    return {"z_lam2":float(z_lam2), "z_tri":float(z_tri),
            "pass": bool((abs(z_lam2)>2.58) or (abs(z_tri)>2.58)), "figs":figs}

def test2_persistence(galaxy_path, subsample=6000, seed=43):
    if not _have_ripser: raise RuntimeError("ripser not installed")
    df = load_table_auto(galaxy_path)
    RA = "RA" if "RA" in df.columns else "ra"
    DEC= "DEC" if "DEC" in df.columns else "dec"
    Z  = "Z" if "Z" in df.columns else "z"
    if len(df)>subsample:
        df = df.sample(n=subsample, random_state=seed)
    chi = DEFAULT_COSMO.comoving_distance(df[Z].to_numpy()).to(u.Mpc).value
    pts = to_cartesian(df[RA].to_numpy(), df[DEC].to_numpy(), chi)
    integ = integrated_persistence(pts, maxdim=1)
    # isotropic null (bootstrap)
    rng = np.random.default_rng(seed)
    null=[]
    for _ in range(25):
        ra  = rng.uniform(0,360,len(df)); dec = np.rad2deg(np.arcsin(rng.uniform(-1,1,len(df))))
        pts0= to_cartesian(ra,dec,chi); null.append(integrated_persistence(pts0, maxdim=1))
    mu,sd = np.mean(null), np.std(null)+1e-12
    z = (integ-mu)/sd
    plt.figure(figsize=(6,4)); plt.hist(null,bins=20,alpha=0.7)
    plt.axvline(integ,c='r',label=f"data z={z:.2f}"); plt.legend()
    figs=[savefig("test2_persistence.png")]
    return {"z":float(z), "pass": bool(z>2.58), "figs":figs}

def test3_phase_locking(cmb_path, lens_path, lmax=10):
    if not _have_healpy: raise RuntimeError("healpy not installed")
    m1 = read_healpix_map(cmb_path); m2 = read_healpix_map(lens_path)
    mask = np.isfinite(m1) & np.isfinite(m2)
    rho_obs = low_ell_phase_corr(m1, m2, lmax=lmax, mask=mask)
    # phase-scramble null
    def scramble(m):
        alm = hp.map2alm(m, lmax=lmax, iter=0); alm_s = np.copy(alm)
        rng = np.random.default_rng(123)
        for l in range(1,lmax+1):
            for mm in range(1,l+1):
                a=hp.Alm.getalm(alm, l,mm); amp=np.abs(a); ph=rng.uniform(-np.pi,np.pi)
                hp.Alm.setalm(alm_s,l,mm, amp*np.exp(1j*ph))
        return hp.alm2map(alm_s, nside=hp.get_nside(m), verbose=False)
    null=[]
    for _ in range(300):
        m2s=scramble(m2); null.append(low_ell_phase_corr(m1,m2s,lmax=lmax,mask=mask))
    null=np.array(null); p_mc=(np.sum(null>=rho_obs)+1)/(len(null)+1)
    plt.figure(figsize=(6,4)); plt.hist(null,bins=30,alpha=0.7)
    plt.axvline(rho_obs,c='r',label=f"obs ρ={rho_obs:.3f}, p={p_mc:.3f}"); plt.legend()
    figs=[savefig("test3_phase.png")]
    return {"rho":float(rho_obs), "p_mc":float(p_mc), "pass": bool(p_mc<0.01), "figs":figs}

def test4_gw_classical(ligo_path, fmin=20.0, fmax=1024.0):
    strain, fs = read_gw_hdf5(ligo_path)
    w = bandpass_whiten(strain, fs, fmin=fmin, fmax=fmax)
    N=len(w); edge=N//5
    off = np.concatenate([w[:edge], w[-edge:]])
    ad = stats.anderson(off, dist='norm')
    ad_ok = ad.statistic < ad.critical_values[min(2,len(ad.critical_values)-1)]
    freqs, Pxx = signal.welch(w, fs=fs, nperseg=4*int(fs))
    bg = signal.medfilt(Pxx, kernel_size=9)
    ratio = (Pxx+1e-20)/(bg+1e-20)
    peaks,_ = signal.find_peaks(ratio, height=1.0)
    if len(peaks)>0:
        pseudo_p = 1/np.maximum(ratio[peaks],1.0000001)
        order=np.argsort(pseudo_p); m=len(pseudo_p); q=0.01
        thresh_idx=-1
        for i,k in enumerate(order, start=1):
            if pseudo_p[k] <= i*q/m: thresh_idx=i
        lines_ok = (thresh_idx==-1)
    else:
        lines_ok=True
    plt.figure(figsize=(8,4)); plt.semilogy(freqs, ratio)
    plt.title("Test 4: Whitened PSD line ratio"); plt.xlabel("Hz"); plt.ylabel("Pxx/bg")
    figs=[savefig("test4_gw_psd_ratio.png")]
    return {"anderson_ok":bool(ad_ok), "lines_ok":bool(lines_ok), "pass": bool(ad_ok and lines_ok), "figs":figs}

def test5_bell(bell_csv, nbins=9):
    df = pd.read_csv(bell_csv)
    for c in ["a","b","x","y"]:
        if c not in df.columns: raise ValueError("Bell CSV must have a,b,x,y")
    a=df["a"].to_numpy(float); b=df["b"].to_numpy(float)
    x=df["x"].to_numpy(float); y=df["y"].to_numpy(float)
    xy=x*y; dth=np.mod(b-a, np.pi)
    bins=np.linspace(0,np.pi, nbins+1); centers=0.5*(bins[:-1]+bins[1:])
    idx=np.digitize(dth,bins)-1
    obs=[]; exp=[]
    for i in range(nbins):
        m=(idx==i); 
        if m.sum()<10: obs.append(np.nan); exp.append(np.nan)
        else:
            obs.append(np.mean(xy[m])); exp.append(-np.cos(centers[i]))
    obs=np.array(obs); exp=np.array(exp)
    mask=np.isfinite(obs)
    rmse=np.sqrt(np.mean((obs[mask]-exp[mask])**2))
    plt.figure(figsize=(6,4))
    plt.plot(centers, exp,'k--',label="QM: -cos Δθ")
    plt.plot(centers, obs,'ro-',label="Observed")
    plt.legend(); plt.title(f"Test 5: RMSE={rmse:.3f}")
    figs=[savefig("test5_bell.png")]
    return {"rmse":float(rmse), "pass": bool(rmse>0.15), "figs":figs}

def test6_decay(decay_csv):
    df = pd.read_csv(decay_csv)
    for c in ["time","counts"]:
        if c not in df.columns: raise ValueError("decay CSV needs time,counts")
    counts = df["counts"].to_numpy()
    windows=[1,5,10,25,50,100,250,500,1000]
    fano=[]; sig=[]
    for w in windows:
        n=len(counts)//w
        if n<5: fano.append(np.nan); sig.append(np.nan); continue
        sums=counts[:n*w].reshape(n,w).sum(axis=1)
        mu=np.mean(sums); var=np.var(sums, ddof=1); F=var/(mu+1e-12)
        fano.append(F); sig.append(np.sqrt(2.0/max(n-1,1)))
    fano=np.array(fano); sig=np.array(sig)
    plt.figure(figsize=(7,4))
    plt.errorbar(windows, fano, yerr=5*sig, fmt='o-')
    plt.axhline(1.0, c='k', ls='--'); plt.xscale('log')
    plt.title("Test 6: Fano vs Poisson ±5σ")
    figs=[savefig("test6_decay.png")]
    ok=False
    for F,S in zip(fano,sig):
        if np.isfinite(F) and np.isfinite(S) and abs(F-1.0)>5*S: ok=True; break
    return {"pass":bool(ok), "figs":figs, "windows":windows, "fano":fano.tolist()}

def test7_rng(qrng_path, sessions_csv=None):
    bits = read_bits_file(qrng_path)
    res={"sessions":[]}
    if sessions_csv is None:
        decision,n,llr = sprt(bits, epsilon=RNG_EPSILON_FLOOR)
        res["sessions"].append({"label":"whole_stream","decision":decision,"tested":int(n),
                                "bias": float(bits.mean()-0.5), "n_total": int(len(bits)),
                                "epsilon": RNG_EPSILON_FLOOR})
        res["pass"] = (decision=="H1")
        return res
    sess = load_sessions_csv(sessions_csv)
    pass_intent=0; n_intent=0; ok_control=0; n_control=0
    for _,row in sess.iterrows():
        s,e,label = int(row["start"]), int(row["end"]), str(row["label"]).lower()
        if s<0 or e>len(bits) or e<=s: continue
        b = bits[s:e]
        eps = RNG_EPSILON_FLOOR
        if ":" in label:
            base,val = label.split(":",1); label=base
            try: eps=float(val)
            except: pass
        decision,n,llr = sprt(b, epsilon=eps)
        res["sessions"].append({"label":label,"decision":decision,"tested":int(n),
                                "bias": float(b.mean()-0.5), "n_total": int(len(b)),
                                "epsilon": eps})
        if label=="intent":
            n_intent+=1; 
            if decision=="H1": pass_intent+=1
        elif label=="control":
            n_control+=1; 
            if decision=="H0": ok_control+=1
    res["pass"] = (n_intent>0 and pass_intent>=1) and (n_control==0 or ok_control>=max(1,n_control//2))
    return res

# ----------------- CLI / Runner -----------------

def resolve_path(key, cli_value):
    """Return a usable path for dataset key, preferring CLI, then env, then download."""
    src = DATA_SOURCES[key]
    # CLI override
    if cli_value:
        p = Path(cli_value)
        return p if p.exists() else None
    # Env or cache/download
    got = try_download(key, src, quiet=False)
    return got

def main():
    ap = argparse.ArgumentParser(description="INT autoload real-data test suite")
    for k,v in DATA_SOURCES.items():
        ap.add_argument(v["flag"], type=str, default=None, help=v["desc"])
    ap.add_argument("--subsample", type=int, default=12000, help="Max galaxies")
    ap.add_argument("--knn", type=int, default=8, help="k for kNN graph")
    ap.add_argument("--lmax", type=int, default=10, help="Low-ℓ max")
    args = ap.parse_args()

    console.print(Panel.fit("[bold cyan]INFORMATION NETWORK THEORY — AUTOLOAD SUITE[/bold cyan]\n"
                            "Uses local files if provided; otherwise downloads public samples.",
                            title="INT Suite", border_style="cyan"))

    # Show theory constants
    t = Table(title="Theory parameters")
    t.add_column("Parameter"); t.add_column("Value")
    t.add_row("E_cycle [J]", f"{E_cycle_J:.3g}")
    t.add_row("S_cycle [bits]", f"{S_cycle_bits:.3g}")
    t.add_row("Layer dilution", f"{LAYER_DILUTION:.3g}")
    t.add_row("Assumed layers", "7")
    console.print(t)

    # Resolve datasets
    paths = {}
    for key in DATA_SOURCES:
        cli_val = getattr(args, key)
        paths[key] = resolve_path(key, cli_val)

    # Summary collector
    summary = []

    # Test 1
    console.rule("[bold]Test 1: Network motifs & spectra[/bold]")
    if paths["galaxies"] is None:
        console.print("[yellow]SKIPPED[/yellow]: galaxies file not available")
        summary.append(("Network motifs", None, {"error":"missing galaxies"}))
    else:
        try:
            r1 = test1_network(paths["galaxies"], subsample=args.subsample, k=args.knn)
            console.print(f"z(λ₂)={r1['z_lam2']:.2f}  z(triangle)={r1['z_tri']:.2f}")
            console.print("[green]PASS[/green]" if r1["pass"] else "[red]FAIL[/red]")
            summary.append(("Network motifs", r1["pass"], r1))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("Network motifs", None, {"error":str(e)}))

    # Test 2
    console.rule("[bold]Test 2: Persistent homology[/bold]")
    if paths["galaxies"] is None:
        console.print("[yellow]SKIPPED[/yellow]: galaxies file not available")
        summary.append(("Persistent homology", None, {"error":"missing galaxies"}))
    elif not _have_ripser:
        console.print("[yellow]SKIPPED[/yellow]: pip install ripser")
        summary.append(("Persistent homology", None, {"error":"ripser missing"}))
    else:
        try:
            r2 = test2_persistence(paths["galaxies"], subsample=min(args.subsample,6000))
            console.print(f"z(H1 persistence)={r2['z']:.2f}")
            console.print("[green]PASS[/green]" if r2["pass"] else "[red]FAIL[/red]")
            summary.append(("Persistent homology", r2["pass"], r2))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("Persistent homology", None, {"error":str(e)}))

    # Test 3
    console.rule("[bold]Test 3: Low-ℓ phase locking[/bold]")
    if not _have_healpy:
        console.print("[yellow]SKIPPED[/yellow]: pip install healpy (py3.13 wheels may lag; py3.12 recommended)")
        summary.append(("Phase locking", None, {"error":"healpy missing"}))
    elif paths["cmb"] is None or paths["lensing"] is None:
        console.print("[yellow]SKIPPED[/yellow]: CMB or lensing map not available")
        summary.append(("Phase locking", None, {"error":"missing maps"}))
    else:
        try:
            r3 = test3_phase_locking(paths["cmb"], paths["lensing"], lmax=args.lmax)
            console.print(f"ρ_low-ℓ={r3['rho']:.3f}  p_MC={r3['p_mc']:.3f}")
            console.print("[green]PASS[/green]" if r3["pass"] else "[red]FAIL[/red]")
            summary.append(("Phase locking", r3["pass"], r3))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("Phase locking", None, {"error":str(e)}))

    # Test 4
    console.rule("[bold]Test 4: GW classicality[/bold]")
    if paths["ligo"] is None:
        console.print("[yellow]SKIPPED[/yellow]: LIGO HDF5 not available")
        summary.append(("GW classicality", None, {"error":"missing LIGO file"}))
    else:
        try:
            r4 = test4_gw_classical(paths["ligo"])
            tags = []
            tags.append("Gaussian off-source ✔" if r4["anderson_ok"] else "Gaussian off-source ✘")
            tags.append("No narrow lines ✔" if r4["lines_ok"] else "Lines detected ✘")
            console.print(", ".join(tags))
            console.print("[green]PASS[/green]" if r4["pass"] else "[red]FAIL[/red]")
            summary.append(("GW classicality", r4["pass"], r4))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("GW classicality", None, {"error":str(e)}))

    # Test 5
    console.rule("[bold]Test 5: Bell residuals[/bold]")
    if paths["bell"] is None:
        console.print("[yellow]SKIPPED[/yellow]: Bell CSV not available")
        summary.append(("Bell residuals", None, {"error":"missing bell CSV"}))
    else:
        try:
            r5 = test5_bell(paths["bell"])
            console.print(f"RMSE={r5['rmse']:.3f}")
            console.print("[green]PASS[/green]" if r5["pass"] else "[red]FAIL[/red]")
            summary.append(("Bell residuals", r5["pass"], r5))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("Bell residuals", None, {"error":str(e)}))

    # Test 6
    console.rule("[bold]Test 6: Radioactive decay memory[/bold]")
    if paths["decay"] is None:
        console.print("[yellow]SKIPPED[/yellow]: decay CSV not available")
        summary.append(("Decay memory", None, {"error":"missing decay CSV"}))
    else:
        try:
            r6 = test6_decay(paths["decay"])
            console.print("PASS if any |F-1| > 5σ_Poisson")
            console.print("[green]PASS[/green]" if r6["pass"] else "[red]FAIL[/red]")
            summary.append(("Decay memory", r6["pass"], r6))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("Decay memory", None, {"error":str(e)}))

    # Test 7
    console.rule("[bold]Test 7: RNG micro-bias[/bold]")
    if paths["qrng"] is None:
        console.print("[yellow]SKIPPED[/yellow]: QRNG bits not available")
        summary.append(("RNG micro-bias", None, {"error":"missing qrng file"}))
    else:
        try:
            r7 = test7_rng(paths["qrng"], paths["sessions"])
            for s in r7["sessions"]:
                console.print(f"[{s['label']}] decision={s['decision']} tested={s['tested']} "
                              f"bias={s['bias']:+.6f} n={s['n_total']}" + (f" eps={s.get('epsilon'):.6g}" if 'epsilon' in s else ""))
            console.print("[green]PASS[/green]" if r7.get("pass",False) else "[red]FAIL[/red]")
            summary.append(("RNG micro-bias", r7.get("pass",False), r7))
        except Exception as e:
            console.print("[yellow]SKIPPED[/yellow]:", e)
            summary.append(("RNG micro-bias", None, {"error":str(e)}))

    # --------- Summary & report ----------
    passed = sum(1 for _,p,_ in summary if p is True)
    total  = sum(1 for _,p,_ in summary if p is not None)
    console.rule("[bold cyan]SUMMARY[/bold cyan]")
    tbl = Table(title="Test outcomes")
    tbl.add_column("Test"); tbl.add_column("Status")
    for name,p,_ in summary:
        status = "[green]PASS[/green]" if p is True else "[red]FAIL[/red]" if p is False else "[yellow]SKIPPED[/yellow]"
        tbl.add_row(name, status)
    console.print(tbl)
    console.print(f"[bold]Total:[/bold] {passed}/{total} evaluated")

    report = {
        "meta": {
            "E_cycle_J": E_cycle_J,
            "S_cycle_bits": S_cycle_bits,
            "layer_dilution": LAYER_DILUTION,
            "assumed_layers": 7
        },
        "paths": {k: (str(v) if v else None) for k,v in paths.items()},
        "summary": [{"test":name,"pass":p,"details":det} for name,p,det in summary]
    }
    (OUTDIR/"INT_report.json").write_text(json.dumps(report, indent=2))
    console.print(Panel.fit(f"Report saved to {OUTDIR/'INT_report.json'}", border_style="green"))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print("[red]FATAL:[/red]", e)
        console.print(traceback.format_exc())
        sys.exit(1)
