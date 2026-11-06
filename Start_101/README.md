# Start_101: IxNetwork automation for new users

A short course: six small Python scripts, each one teaching a single concept,
ordered from "hello world" to MACsec with MKA. Each script stands on its own,
so you can run any of them directly.

All scripts use **RestPy** (`ixnetwork-restpy`), the official Python client for the
IxNetwork REST API. It runs unchanged against the Windows IxNetwork GUI, the Linux API
server and IxNetwork Web Edition.

| # | Script | You learn |
|---|--------|-----------|
| 01 | `01_create_and_delete_session.py` | Connect, give the session a unique name, explore the object tree, **always delete the session** |
| 02 | `02_load_saved_config.py` | Load an `.ixncfg` built in the GUI, remap ports, run, check loss, export CSV |
| 03 | `03_build_l2l3_from_scratch.py` | Topology → DeviceGroup → Ethernet → IPv4, multivalues, traffic items |
| 04 | `04_macsec_static_sak.py` | MACsec (802.1AE) with static SAKs, encrypted traffic, a frame-size sweep, MACsec stats |
| 05 | `05_macsec_mka.py` | MACsec with MKA (CAK/CKN, key server, rekey options), verifying MKA, encrypted traffic |
| 06 | `06_capture_save_and_report.py` | Data/control-plane capture, downloading `.cap` files, saving the config, reports |
| – | `common.py` | Shared helpers: session context manager, port mapping, stats to CSV, `describe()` |
| – | `lab_config.py` | **The only file you edit**: API server, chassis, ports, credentials |
| – | `MCP_SERVER.md` | Driving IxNetwork in plain English from Claude through an MCP server |

## 1. Setup

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

Then edit `lab_config.py`, or set environment variables instead:

```bash
export IXN_API_SERVER=localhost      # IxNetwork GUI on this PC; or the Linux API server / Web Edition IP
export IXN_CHASSIS=10.80.81.2
export IXN_PASSWORD='********'       # never commit passwords
```

## 2. Run the lessons in order

```bash
python 01_create_and_delete_session.py
```

```bash
python 02_load_saved_config.py configs/my_test.ixncfg
```

```bash
python 03_build_l2l3_from_scratch.py
```

```bash
python 04_macsec_static_sak.py
```

```bash
python 05_macsec_mka.py
```

```bash
python 06_capture_save_and_report.py configs/my_test.ixncfg
```

Each script writes its outputs to `results/`: the RestPy log, CSV statistics, captures
and saved configs.

## 3. Rules that save you pain

1. **Delete your session.** Sessions hold licenses and port ownership. Every script
   cleans up in a `finally:` block. To keep a session open for debugging in the Web UI,
   set `IXN_KEEP_SESSION=1`, then delete the session yourself afterwards.
2. **Give sessions unique names.** Names look like `start101-<user>-<timestamp>`, so
   anyone can see who owns which session. On the Windows GUI there is only one session,
   and the name is ignored.
3. **Build in the GUI, automate with a script.** Prototype the test interactively, save
   it as `.ixncfg`, and load it from the script (lesson 02). Move to from-scratch builds
   (lessons 03–05) once you need parameter sweeps.
4. **Learn the API from the GUI.**
   * `describe(obj)` in `common.py` prints every property and method of an object.
   * The REST API browser at `https://<api-server>/api/v1/sessions/<id>/ixnetwork/` shows the live tree.
   * Set `LOG_LEVEL='request'` to log every REST call a script makes.
5. **Multivalues.** Any per-device field (MAC, IP, VLAN, key, ...) takes `.Single(v)`,
   `.Increment(start_value, step_value)`, `.ValueList([...])` or `.Random()`. One line can
   configure 1 or 10,000 devices.

## 4. MACsec notes for the lab DUT (NXP TSN switch)

* **Static SAK (lesson 04).** The DUT interfaces need the **same SAK and cipher suite**
  as the test ports. If the DUT terminates MACsec hop by hop, set `DUT_MACS` to the DUT
  interface MACs.
* **MKA (lesson 05).** The **CAK/CKN** must match the DUT. `KEY_SERVER_PRIORITY` decides
  who becomes key server: the lower value wins. Set 255 on both test ports to make the
  DUT the key server.
* **Rate headroom.** MACsec adds a 16-byte SecTAG (or 8 bytes without the SCI) and a
  16-byte ICV to every frame. At 64-byte frames that is a large share of the line rate,
  so the samples run at 90% by default.
* **Statistics.** Look for the *MACsec* and *MKA* statistic views. The scripts find them
  by name (`list_views(session, 'mka')`) and export them to CSV.

## 5. Where to find the API reference

* **The API server.** Every IxNetwork API server documents its own REST API, matching
  your installed version: `https://<api-server>/api/v1/...`. In the GUI, use
  *Help → API Docs / REST API Browser*.
* **RestPy documentation and samples.** <https://github.com/OpenIxia/ixnetwork_restpy>
  and <https://pypi.org/project/ixnetwork-restpy/>.
* **More examples.** `../RestPy/SampleScripts` in this repository: BGP, EVPN, VXLAN,
  QuickTest, capture, and more.
* **Legacy APIs.** `../LowLevelApi/NGPF/Python/L2 Security` has the older Low-Level API
  MACsec samples. They are useful for reference, but use RestPy for new work.
