<template>
  <div>
  <pdf ref="myPdfComponent" src="./static/xkbproto.pdf"></pdf>
      <button @click="$refs.myPdfComponent.print()">print</button>
  </div>
</template>

<script>
import pdf from 'vue-pdf'

export default {
  components: {
    pdf
  }
}
</script>