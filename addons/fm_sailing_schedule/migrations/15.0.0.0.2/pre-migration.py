
def migrate(cr, registry):
    cr.execute("""
            DELETE FROM freight_schedule
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM freight_schedule
                WHERE voyage_number IS NOT NULL
                GROUP BY voyage_number
            )
        """)
