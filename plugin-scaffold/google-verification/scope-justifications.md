# Restricted scope justifications

Paste this language into the Google verification form. It describes what the product does. It is not a statement that verification has been submitted.

## gmail.readonly

WisdomTwin is a business role twin. A customer connects a company Gmail account so the current officeholder of a role, such as Chief Revenue Officer, can ask questions about business email. WisdomTwin reads messages the user already has access to, chunks them, stores embeddings plus a short excerpt for citations, and deletes the raw provider payload when the ingestion job finishes.

The scope is `https://www.googleapis.com/auth/gmail.readonly`. WisdomTwin does not send, delete, label, or modify mail. A narrower scope cannot see the message text the citation has to quote. Consumer Gmail domains are rejected before a grant is offered.

## drive.readonly

The same role twin reads business files the connected account can already open, so an answer can cite a document. The scope is `https://www.googleapis.com/auth/drive.readonly`. WisdomTwin does not create, edit, share, or delete files. Metadata alone cannot supply the excerpt a citation needs, so the read-only scope is the one that matches the product.

## What reviewers can watch

Use a test user on a managed business domain. Connect the role title, run an ingestion of a few messages or files, and ask a question. The answer should quote only ingested material and show a citation. There is no send button and no write call in this build.
