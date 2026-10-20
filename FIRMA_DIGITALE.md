# Firma digitale di LeggiTutto

Windows e macOS mostrano un avviso ("editore sconosciuto", "sviluppatore non identificato") per i programmi senza firma digitale. Per toglierlo serve un **certificato di firma del codice** intestato all'autore, Massimiliano Mascioli Trippa. Il certificato lo rilascia un ente autorizzato dopo aver verificato l'identità, quindi va richiesto personalmente: non si può creare dal progetto né ottenere a nome di qualcun altro.

Il progetto è già pronto per la firma: una volta ottenuti i certificati basta inserirli su GitHub come "secrets" e avviare la compilazione. I file pubblicati vengono firmati automaticamente.

## macOS: Apple Developer Program (consigliato)

Costo: 99 € circa all'anno. Con questa firma l'app viene anche "notarizzata" da Apple e si apre senza nessun avviso.

1. Iscriviti come persona fisica su [developer.apple.com/programs](https://developer.apple.com/programs/) con il tuo ID Apple. Il nome che compare come sviluppatore sarà quello dell'iscrizione.
2. Da un Mac, apri Xcode, vai in Impostazioni, poi Account, poi Gestisci certificati, e crea un certificato **Developer ID Application**. In alternativa crealo dal sito developer.apple.com, sezione Certificates.
3. Apri Accesso Portachiavi, seleziona il certificato "Developer ID Application: Massimiliano Mascioli Trippa", scegli Esporta e salvalo come file `.p12` con una password.
4. Da Terminale copia il certificato in formato testo: `base64 -i certificato.p12 | pbcopy`
5. Su [appleid.apple.com](https://appleid.apple.com), nella sezione Accesso e sicurezza, crea una **password specifica per l'app**.
6. Il **Team ID** (10 caratteri) si trova su developer.apple.com, sezione Membership.
7. Su GitHub apri il repository e vai in Settings, poi Secrets and variables, poi Actions, poi New repository secret. Aggiungi:

| Nome del secret | Contenuto |
|---|---|
| `MACOS_CERTIFICATE` | il testo copiato al punto 4 |
| `MACOS_CERTIFICATE_PASSWORD` | la password scelta al punto 3 |
| `APPLE_ID` | l'indirizzo email del tuo ID Apple |
| `APPLE_TEAM_ID` | il Team ID del punto 6 |
| `APPLE_APP_PASSWORD` | la password specifica del punto 5 |

8. Avvia di nuovo la compilazione (scheda Actions, "Compila LeggiTutto", Run workflow).

## Windows

Dal 2023 i certificati di firma devono essere custoditi su un dispositivo sicuro (chiavetta crittografica o servizio in cloud). Le strade possibili sono:

- **Certum Open Source Code Signing** (Certum, Polonia): certificato economico rilasciato a sviluppatori privati di software open source, con il tuo nome come editore. La firma si fa dal tuo PC con il programma SimplySign. Informazioni su [certum.eu](https://www.certum.eu).
- **SignPath Foundation**: gratuita per i progetti open source pubblici, firma in automatico su GitHub. Come editore però compare "SignPath Foundation" e non il tuo nome. Richiede una licenza open source riconosciuta (per esempio MIT o GPL). Informazioni su [signpath.org](https://signpath.org).
- **Microsoft Azure Artifact Signing** (ex Trusted Signing): costa poco, ma per i privati è disponibile solo negli Stati Uniti e in Canada. In Europa è riservata alle organizzazioni registrate.

Anche con la firma, Windows SmartScreen può mostrare un avviso per le prime settimane, finché il programma non accumula una "reputazione" di download.

Una volta scelto il certificato, il passaggio di firma va aggiunto al flusso `.github/workflows/build.yml`.

## Verifica dell'integrità

Ogni Release contiene il file `SHA256SUMS.txt` con le impronte digitali dei file di installazione. Servono a verificare che un file scaricato sia identico a quello pubblicato:

- Windows: `certutil -hashfile LeggiTutto-Windows-Setup.exe SHA256`
- Mac: `shasum -a 256 LeggiTutto-macOS-AppleSilicon.dmg`
