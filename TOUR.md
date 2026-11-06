# Actual integrated-image boot tour

These are unaltered guest captures. No usable desktop or installer release is claimed. For every capture and report, extract the archive and open index.html.

## Live account creation, hidden entry

Actual UEFI guest console. The temporary owner password is created locally; no online account is required. Both entries were concealed in this observed console redraw.

![Actual guest capture](images/f1aa4c522af8b852e0c600ea967ebc651284fe4d9e630433215c89a58058b8c3.png)

## Actual OREZ graphical login

Actual SDDM in the booted ISO, with the approved wallpaper. The initial session label still carries upstream branding. This is a login screen, not the desktop.

![Actual guest capture](images/42b44dedde297345d164e52c95fd6c8884ab7a7a2096ece5ac8b4e83d396d408.png)

## Owner authentication and administrator boundary

Actual owner shell, UID 1000. Passwordless sudo is refused; SDDM is active. This is a scoped authorization check, not a comprehensive security certification.

![Actual guest capture](images/f80b2d303dd1e905ec6f59a0806788c89284ac3ab525d102c372a9f6b5db0c42.png)

## Fourth boot owner shell

Despite its historical filename, this is tty2 after successful ordinary owner authentication. Earlier partial captures did not prove a rejected password.

![Actual guest capture](images/1c24bd9dd490c52ab2b0d6b23d4de3d5ddf5804e377fa0e08e85ca6e34eae000.png)

## Desktop remains blocked

The third boot authenticated through SDDM/PAM and started Plasma, but the observed desktop stayed black. This failed observation is retained.

![Actual guest capture](images/05713dbacb00cfa92e8cad1581147b0f1349f6ee14c97d122440aff36011bd53.png)
