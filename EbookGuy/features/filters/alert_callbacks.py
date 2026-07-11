import ast

from database.filters_mdb import find_filter
from database.gfilters_mdb import find_gfilter


async def maybe_handle_alert_callback(client, query):
    if "gfilteralert" in query.data:
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        _, _, alerts, _ = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        _, _, alerts, _ = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    else:
        return False
    return True
