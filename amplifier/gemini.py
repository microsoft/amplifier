#!/usr/bin/env python3
import click

@click.group()
def cli():
    """A command-line tool for interacting with the Gemini API."""
    pass

@cli.command()
def hello():
    """Prints a simple hello message."""
    click.echo("Hello from Gemini!")

if __name__ == '__main__':
    cli()
