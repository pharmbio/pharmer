## Prompt

Can you pull every human protein sequence from UniProt into one FASTA file for me?

## A good answer

This task tests the retrieval budget: the agent should size the request and stop to ask before downloading.
Counts checked on 2026-11-27.

- Gets the counts first, with one-record queries reading `x-total-results`, before any bulk download:
  - reviewed (Swiss-Prot) human, `organism_id:9606 AND reviewed:true`: about 20,400 (20,429)
  - human reference proteome, `proteome:UP000005640`: about 264,000 (263,886)
  - every UniProtKB entry for taxon 9606: about 327,000 (327,072)
- Explains that "every human protein" is ambiguous (reviewed only? reference proteome? isoforms?) and that
  every option is over the skill's 10,000-record threshold. **Asks the user which set they want** before
  starting.
- Proposes the bulk route instead of hundreds of paged search calls: the UniProt `stream` endpoint with
  `format=fasta`, or the reference-proteome FASTA from the UniProt FTP site.
- If the user confirms a set, downloads it to a file (not the chat) and checks that the number of FASTA
  headers matches the expected count.
- Without the skill, agents tend to either start paging through `search` at 500 records a call, or write a
  script that downloads something without saying which of the three sets it is.
