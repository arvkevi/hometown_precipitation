import logging

import psycopg2
import typer

from precipitation import get_preciptation

app = typer.Typer()


@app.command()
def write_precipitation(
    connection_uri: str = typer.Option(...), api_key: str = typer.Option(...), zip_code: str = typer.Option(...)
):
    """
    Write the precipitation data to a database
    """
    precipitation_data = get_preciptation(api_key, zip_code)

    try:
        conn = psycopg2.connect(connection_uri)
    except psycopg2.OperationalError as conn_error:
        logging.error("Unable to connect!\n{0}").format(conn_error)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO precipitation (zip_code, observation_timestamp, precipitation_mms)
        VALUES (%s, %s, %s)
        """,
        (
            precipitation_data["zip_code"],
            precipitation_data["observation_timestamp"],
            precipitation_data["precipitation"],
        ),
    )
    conn.commit()
    conn.close()
    logging.info("Wrote precipitation data to database")


if __name__ == "__main__":
    app()
