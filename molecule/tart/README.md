# Tart Molecule scenario

This scenario is a *local harness* for running the role against a Tart VM.

## Does Molecule support Tart directly?

Molecule does not ship with a built-in Tart driver (like `docker` or `vagrant`).
This scenario uses the **delegated** driver, plus scenario playbooks that call the `tart` CLI to:

- create a VM (import or clone)
- start it
- discover its IP (`tart ip`)
- run the role via SSH
- stop and delete the VM

## SSH requirements

This scenario is configured for **password-based SSH** by default (`vagrant/vagrant`).
That means the controller (your macOS host) must have `sshpass` available.

## Automated usage

### Option A: Import from a .tvm

```bash
cd "$(git rev-parse --show-toplevel)"

MOLECULE_TART_IMPORT_TVM=/path/to/your-image.tvm \
MOLECULE_TART_VM=rocky101-molecule \
MOLECULE_TART_USER=vagrant \
MOLECULE_TART_PASSWORD=vagrant \
molecule test -s tart
```

### Option B: Clone an existing Tart VM template

If you already have a base VM imported (for example `rocky101`), clone it:

```bash
cd "$(git rev-parse --show-toplevel)"

MOLECULE_TART_SOURCE_VM=rocky101 \
MOLECULE_TART_VM=rocky101-molecule \
MOLECULE_TART_USER=vagrant \
MOLECULE_TART_PASSWORD=vagrant \
molecule test -s tart
```

## Notes

- By default `molecule/tart/converge.yml` uses `tart_guest_agent_install_method: auto`.
  Override with `MOLECULE_TART_AGENT_METHOD=repo` or `MOLECULE_TART_AGENT_METHOD=github`.
- Cleanup is handled automatically (scenario runs `destroy`).

## What it verifies

- Role runs successfully
- Tart guest agent selection logic is invoked by `target_tart: true`
- A guest agent package is installed (service enable/start is best-effort)
