import csv
import click


@click.command()
@click.argument('csvfile')
def kuweiprocess(csvfile):
    with open(csvfile) as f:
        reader = csv.reader(f)
        locale = None
        result = []
        for row in reader:
            # Create a new record
            if '-' in row[0]:
                locale = row[0]
                continue
            result.append(row[0] + ',' + locale)
    for r in result:
        print(r)


@click.group()
def cli():
    pass


cli.add_command(kuweiprocess)

if __name__ == '__main__':
    cli()
