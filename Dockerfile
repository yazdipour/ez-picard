FROM tscholak/text-to-sql-eval:6a252386bed6d4233f0f13f4562d8ae8608e7445

COPY src /app/seq2seq

# Banner
RUN pip install pyfiglet
RUN echo "pyfiglet EZ-PICARD" > /etc/update-motd.d/00-header